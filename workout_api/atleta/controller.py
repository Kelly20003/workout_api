import traceback
from datetime import datetime
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Body, status, HTTPException, Query
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from fastapi_pagination import Page, paginate
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaResumido
from workout_api.atleta.models import AtletaModel
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency


router = APIRouter()

@router.post(
    '/',
    summary='Criar um novo atleta',
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut,
)
async def post(
    db_session: DatabaseDependency,
    atleta_in: AtletaIn = Body(...)
):
    categoria_nome = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome

    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_nome))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'A categoria {categoria_nome} não foi encontrada.'
        )

    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome))
    ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'O centro de treinamento {centro_treinamento_nome} não foi encontrado.'
        )

    try:
        atleta = AtletaModel(
            id=uuid4(),
            nome=atleta_in.nome,
            cpf=atleta_in.cpf,
            idade=atleta_in.idade,
            peso=atleta_in.peso,
            altura=atleta_in.altura,
            sexo=atleta_in.sexo,
            created_at=datetime.utcnow(),
            categoria_id=categoria.pk_id,
            centro_treinamento_id=centro_treinamento.pk_id
        )
        db_session.add(atleta)
        await db_session.commit()
        await db_session.refresh(atleta) 

    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}"
        )
    except Exception as e:
        await db_session.rollback()
        traceback.print_exc()  # <-- Adicionado aqui
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ocorreu um erro ao inserir os dados no banco: {e}'
        )

    return atleta


@router.get(
    '/',
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaResumido],
)
async def get_all(
    db_session: DatabaseDependency,
    nome: Optional[str] = Query(None, description="Filtrar por nome do atleta"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF do atleta")
) -> Page[AtletaResumido]:

    query = select(AtletaModel)

    if nome:
        query = query.filter(AtletaModel.nome == nome)

    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)

    atletas = (await db_session.execute(query)).scalars().all()

    atletas_resumidos = [
        AtletaResumido(
            nome=atleta.nome,
            centro_treinamento=atleta.centro_treinamento.nome,
            categoria=atleta.categoria.nome
        ) for atleta in atletas
    ]
    
    return paginate(atletas_resumidos)


@router.get(
    '/{id}',
    summary='Consulta um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def get(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrado no id: {id}'
        )

    return atleta


@router.patch(
    '/{id}',
    summary='Editar um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def patch(id: UUID4, db_session: DatabaseDependency, atleta_up: AtletaUpdate = Body(...)) -> AtletaOut:
    atleta = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrado no id: {id}'
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
    '/{id}',
    summary='Deletar um Atleta pelo id',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrado no id: {id}'
        )

    try:
        db_session.delete(atleta)
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ocorreu um erro ao deletar o atleta: {e}'
        )
