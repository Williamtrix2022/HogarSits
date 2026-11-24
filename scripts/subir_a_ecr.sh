#!/usr/bin/env bash
# Sube la imagen de producción a Amazon ECR (#45).
#
#   scripts/subir_a_ecr.sh [etiqueta]      # por defecto, el SHA corto del commit actual
#
# Requisitos: Docker y AWS CLI con credenciales de un usuario/rol con permisos de ECR
# (ver docs/aws/IMAGEN_DOCKER.md). Variables opcionales: AWS_REGION (us-east-1), ECR_REPOSITORY
# (hogarsits).
#
# ⚠️ Este script NO se ha probado contra una cuenta real de AWS (se escribió sin credenciales);
# lo que sí se probó es la construcción y el arranque de la imagen. Léalo antes de ejecutarlo.
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
REPO="${ECR_REPOSITORY:-hogarsits}"
ETIQUETA="${1:-$(git rev-parse --short HEAD)}"

CUENTA="$(aws sts get-caller-identity --query Account --output text)"
REGISTRO="${CUENTA}.dkr.ecr.${REGION}.amazonaws.com"
echo "Cuenta ${CUENTA} · región ${REGION} · repositorio ${REPO} · etiqueta ${ETIQUETA}"

# El repositorio se crea una sola vez: analiza vulnerabilidades al subir y las etiquetas no se
# pueden pisar (cada versión es identificable por su commit).
if ! aws ecr describe-repositories --repository-names "${REPO}" --region "${REGION}" >/dev/null 2>&1; then
    aws ecr create-repository --repository-name "${REPO}" --region "${REGION}" \
        --image-scanning-configuration scanOnPush=true \
        --image-tag-mutability IMMUTABLE \
        --encryption-configuration encryptionType=AES256
    # Conserva solo las 10 imágenes más recientes: el almacenamiento de ECR se paga por GB.
    aws ecr put-lifecycle-policy --repository-name "${REPO}" --region "${REGION}" \
        --lifecycle-policy-text '{"rules":[{"rulePriority":1,"description":"conservar las 10 ultimas","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":10},"action":{"type":"expire"}}]}'
fi

docker build -f Dockerfile.prod -t "${REPO}:${ETIQUETA}" .
aws ecr get-login-password --region "${REGION}" | docker login --username AWS --password-stdin "${REGISTRO}"
docker tag "${REPO}:${ETIQUETA}" "${REGISTRO}/${REPO}:${ETIQUETA}"
docker push "${REGISTRO}/${REPO}:${ETIQUETA}"
echo "Imagen subida: ${REGISTRO}/${REPO}:${ETIQUETA}"
