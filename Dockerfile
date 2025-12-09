ARG ECR_URI
FROM ${ECR_URI}/docker-images-python-backend-arm64:latest

ENV FLASK_ENV=production
ENV PORT=<<porta do container - ex:5000 - consultar a planilha das aplicações que estao rodando na AWS>>
ENV APP=nome_do_projeto.app:create_app

COPY nome_do_projeto /app
WORKDIR /app

EXPOSE $PORT

CMD ["waitress-serve", "--port=$PORT", "--url-scheme", "https", "--call", "nome_do_projeto.app:create_app"]
