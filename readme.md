# 🚀 CI/CD Pipeline: FastAPI + Docker + GitHub Actions + ArgoCD

![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions%20%7C%20ArgoCD-blueviolet?style=for-the-badge&logo=githubactions)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Deployed-blue?style=for-the-badge&logo=kubernetes)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

Este projeto implementa uma pipeline de CI/CD completa e automatizada, demonstrando um fluxo de trabalho **GitOps** moderno. A aplicação, desenvolvida em **FastAPI**, é containerizada com **Docker**, integrada via **GitHub Actions** e implantada continuamente em um cluster **Kubernetes** gerenciado pelo **ArgoCD**.


## Arquitetura

A solução é dividida em dois repositórios no GitHub:

1.  **`fastapi-app`**: Contém o código-fonte da aplicação FastAPI, o `Dockerfile` para containerização e o workflow do GitHub Actions que orquestra o pipeline de CI.
2.  **`k8s-manifests`**: Contém os manifestos de `Deployment` e `Service` do Kubernetes. Este repositório é o "source of truth" para o ArgoCD. O pipeline de CI atualiza os manifestos neste repositório automaticamente.

## Fluxo do Pipeline

1.  Um `push` na branch `main` do repositório `fastapi-app` dispara o workflow do GitHub Actions.
2.  A Action faz o checkout do código.
3.  Uma imagem Docker é construída e enviada para o Docker Hub com duas tags: `latest` e o `SHA` do commit.
4.  A Action faz o checkout do repositório `k8s-manifests`.
5.  A tag da imagem no arquivo `deployment.yaml` é atualizada com o `SHA` do novo commit.
6.  A Action cria um Pull Request no repositório `k8s-manifests` com a alteração.
7.  Após o merge do PR, o ArgoCD detecta a mudança no repositório `k8s-manifests`.
8.  O ArgoCD sincroniza o estado do cluster com o manifesto atualizado, realizando o deploy da nova versão da aplicação automaticamente.

---

## Passo a Passo Completo

Siga os passos abaixo para configurar todo o ambiente.

### 1. Criar a Aplicação FastAPI

#### 1.1. Criar Repositórios no GitHub

Crie dois repositórios **públicos** na sua conta do GitHub:

-   `fastapi-app` — Para o código da aplicação, Dockerfile e workflow.
-   `k8s-manifests` — Para os arquivos de manifesto do Kubernetes.

#### 1.2. Criar o Código da Aplicação

Clone o repositório `fastapi-app` para sua máquina local:

```bash
git clone https://github.com/<seu-usuario-github>/fastapi-app.git
cd fastapi-app
```

Crie o arquivo `app.py` com o seguinte conteúdo:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"msg": "Olá Mundo! Esta é uma mensagem inicial."}
```

#### 1.3. Criar o Dockerfile

Na raiz do repositório `fastapi-app`, crie o arquivo `Dockerfile`:

```dockerfile
FROM python:3.11-alpine

WORKDIR /app

RUN pip install fastapi uvicorn

COPY app.py .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Configurar GitHub Actions para CI/CD

#### 2.1. Criar Estrutura de Pastas

Dentro do repositório `fastapi-app`, crie a estrutura de diretórios para os workflows:

```bash
mkdir -p .github/workflows
```

#### 2.2. Criar Workflow CI/CD

Crie o arquivo `.github/workflows/ci-cd.yml` e adicione o conteúdo abaixo. **Lembre-se de substituir `<seu-usuario-github>` pelo seu nome de usuário do GitHub.**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout fastapi-app
        uses: actions/checkout@v4

      - name: Login no Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_ACCESS_TOKEN }}

      - name: Build e push da imagem Docker
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/fastapi-app:latest
            ${{ secrets.DOCKER_USERNAME }}/fastapi-app:${{ github.sha }}

      - name: Checkout repo dos manifests Kubernetes
        uses: actions/checkout@v4
        with:
          repository: <seu-usuario-github>/k8s-manifests
          token: ${{ secrets.GITHUB_PAT }}
          path: k8s-manifests

      - name: Atualizar imagem no manifesto e commitar
        run: |
          cd k8s-manifests
          sed -i "s|image: .*/fastapi-app:.*|image: ${{ secrets.DOCKER_USERNAME }}/fastapi-app:${{ github.sha }}|g" deployment.yaml
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"
          git add deployment.yaml
          git commit -m "Atualizar imagem fastapi-app para ${{ github.sha }}" || echo "Nada para commitar"
          git push
```

> **Nota:** A action `peter-evans/create-pull-request` foi removida em favor de um `git push` direto para simplificar o fluxo. Se preferir o fluxo com Pull Request, pode usar a versão original do seu passo a passo.

#### 2.3. Configurar Secrets no GitHub

No repositório `fastapi-app`, vá em `Settings > Secrets and variables > Actions` e clique em `New repository secret` para adicionar os seguintes secrets:

| Nome                  | Valor                                                              |
| --------------------- | ------------------------------------------------------------------ |
| `DOCKER_USERNAME`     | Seu nome de usuário do Docker Hub.                                 |
| `DOCKER_ACCESS_TOKEN` | Um Token de Acesso do Docker Hub. |
| `GITHUB_PAT`          | Um Personal Access Token (classic) com escopo `repo`. |

### 3. Criar os Manifestos Kubernetes

Clone o repositório `k8s-manifests` e crie os arquivos de manifesto. **Lembre-se de substituir `<seu-usuario-dockerhub>` pelo seu nome de usuário do Docker Hub.**

#### 3.1. `deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-deployment
  labels:
    app: fastapi-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
        - name: fastapi-app
          image: <seu-usuario-dockerhub>/fastapi-app:initial # Esta tag será substituída pelo pipeline
          ports:
            - containerPort: 8000
```

#### 3.2. `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app-service
spec:
  selector:
    app: fastapi-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

Faça o commit e push desses arquivos para o repositório `k8s-manifests`.

### 4. Configurar ArgoCD

#### 4.1. Instalar ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

#### 4.2. Expor e Acessar a UI do ArgoCD

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Acesse a UI no navegador: https://localhost:8080

#### 4.3. Obter a Senha Inicial

O usuário padrão é `admin`. Obtenha a senha com o comando:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
```

#### 4.4. Criar a Aplicação no ArgoCD

1.  Na UI do ArgoCD, clique em **NEW APP**.
2.  Preencha os campos:
    -   **Application Name**: `fastapi-app`
    -   **Project Name**: `default`
    -   **Sync Policy**: `Automatic`
3.  Configure a origem (Source):
    -   **Repository URL**: `https://github.com/<seu-usuario-github>/k8s-manifests.git`
    -   **Revision**: `main`
    -   **Path**: `.`
4.  Configure o destino (Destination):
    -   **Cluster URL**: `https://kubernetes.default.svc`
    -   **Namespace**: `default`
5.  Clique em **CREATE**. O ArgoCD irá clonar o repositório e aplicar os manifestos.

### 5. Testar o Fluxo Completo

#### 5.1. Expor a Aplicação Localmente (usando a porta 8081)

Use `port-forward` para acessar o serviço da sua aplicação:

```bash
kubectl port-forward svc/fastapi-app-service 8081:80
```

Acesse no navegador: http://localhost:8081/. Você deverá ver a mensagem inicial:

```json
{ "msg": "Olá Mundo! Esta é uma mensagem inicial." }
```

#### 5.2. Modificar a Aplicação para Testar a Atualização

No repositório `fastapi-app`, edite o arquivo `app.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"msg": "Atualização feita! Tudo funcionando! 🎉"}
```

Faça o commit e push para a branch `main`:

```bash
git add app.py
git commit -m "Mensagem atualizada para teste de CI/CD"
git push origin main
```

#### 5.3. Acompanhar o Pipeline

-   Vá para a aba "Actions" no repositório `fastapi-app` para ver o pipeline rodando.
-   Após a conclusão, verifique o repositório `k8s-manifests` e veja que um novo commit foi feito pelo "GitHub Actions Bot".
-   Na UI do ArgoCD, observe que ele detectará a mudança (Out of Sync) e iniciará a sincronização automaticamente, atualizando os pods no cluster.

#### 5.4. Verificar a Atualização no Navegador

Recarregue a página http://localhost:8081/. A nova mensagem deve aparecer:

```json
{ "msg": "Atualização feita! Tudo funcionando! 🎉" }
```

---

Parabéns! Você configurou com sucesso um pipeline CI/CD completo com GitOps.



