from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)

    
# __name__ = '__main__' significa que quando o app.run é executado direto da linha
#  de comando ele executa a função main. se ele for importado ele não executa