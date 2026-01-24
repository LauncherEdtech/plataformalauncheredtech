# add_resgate_columns.py - Execute este script para adicionar os novos campos ao modelo Resgate
from app import create_app, db
from sqlalchemy import text
from datetime import datetime, timedelta
import pytz

def extract_contact_info(resgate):
    """Extrai informações de contato do campo endereco_entrega"""
    try:
        if not resgate.endereco_entrega:
            return
            
        lines = resgate.endereco_entrega.replace('<br>', '\n').split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Nome:') and not resgate.nome_contato:
                resgate.nome_contato = line.replace('Nome:', '').strip()
            elif line.startswith('Email:') and not resgate.email_contato:
                resgate.email_contato = line.replace('Email:', '').strip()
            elif (line.startswith('WhatsApp:') or line.startswith('Telefone:')) and not resgate.telefone_contato:
                resgate.telefone_contato = line.replace('WhatsApp:', '').replace('Telefone:', '').strip()
                
    except Exception as e:
        print(f"    ⚠️  Erro ao extrair contato do resgate {resgate.id}: {str(e)}")

def populate_existing_data():
    """Popula dados existentes com valores baseados no status atual"""
    try:
        from app.models.shop import Resgate
        
        # Definir timezone do Brasil
        timezone_brasil = pytz.timezone('America/Sao_Paulo')
        
        print("  → Processando resgates com status 'Enviado'...")
        resgates_enviados = Resgate.query.filter_by(status='Enviado').filter(
            Resgate.data_envio.is_(None)
        ).all()
        
        for resgate in resgates_enviados:
            # Calcular data de envio (1-3 dias após o resgate)
            dias_envio = 1 if resgate.data_resgate.weekday() < 4 else 3  # Mais rápido em dias úteis
            data_envio = resgate.data_resgate + timedelta(days=dias_envio)
            resgate.data_envio = data_envio
            
            # Extrair informações de contato do endereco_entrega se disponível
            if resgate.endereco_entrega and "Nome:" in resgate.endereco_entrega:
                extract_contact_info(resgate)
                
        print(f"    ✓ {len(resgates_enviados)} resgates enviados atualizados")
        
        print("  → Processando resgates com status 'Entregue'...")
        resgates_entregues = Resgate.query.filter_by(status='Entregue').filter(
            Resgate.data_entrega.is_(None)
        ).all()
        
        for resgate in resgates_entregues:
            # Calcular data de entrega (5-7 dias após o resgate)
            dias_entrega = 5 if resgate.data_resgate.weekday() < 4 else 7
            data_entrega = resgate.data_resgate + timedelta(days=dias_entrega)
            resgate.data_entrega = data_entrega
            
            # Se não tiver data de envio, adicionar também
            if not resgate.data_envio:
                dias_envio = 2 if resgate.data_resgate.weekday() < 4 else 3
                resgate.data_envio = resgate.data_resgate + timedelta(days=dias_envio)
            
            # Extrair informações de contato
            if resgate.endereco_entrega and "Nome:" in resgate.endereco_entrega:
                extract_contact_info(resgate)
                
        print(f"    ✓ {len(resgates_entregues)} resgates entregues atualizados")
        
        # Processar resgates pendentes para extrair informações de contato
        print("  → Processando resgates pendentes...")
        resgates_pendentes = Resgate.query.filter_by(status='Pendente').filter(
            Resgate.nome_contato.is_(None)
        ).all()
        
        for resgate in resgates_pendentes:
            if resgate.endereco_entrega and "Nome:" in resgate.endereco_entrega:
                extract_contact_info(resgate)
                
        print(f"    ✓ {len(resgates_pendentes)} resgates pendentes atualizados")
        
        db.session.commit()
        print("  ✓ Dados populados com sucesso!")
        
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Erro ao popular dados: {str(e)}")

def main():
    """Função principal que executa o processo de atualização"""
    app = create_app()
    with app.app_context():
        try:
            print("Iniciando processo de atualização da tabela 'resgate'...")
            print("=" * 60)
            
            # Lista de colunas para verificar e adicionar
            columns_to_add = [
                {
                    'name': 'data_envio',
                    'type': 'TIMESTAMP WITHOUT TIME ZONE',
                    'description': 'Data real de envio do produto'
                },
                {
                    'name': 'data_entrega', 
                    'type': 'TIMESTAMP WITHOUT TIME ZONE',
                    'description': 'Data real de entrega do produto'
                },
                {
                    'name': 'nome_contato',
                    'type': 'VARCHAR(255)',
                    'description': 'Nome do contato para entrega'
                },
                {
                    'name': 'email_contato',
                    'type': 'VARCHAR(255)', 
                    'description': 'Email do contato para entrega'
                },
                {
                    'name': 'telefone_contato',
                    'type': 'VARCHAR(20)',
                    'description': 'Telefone do contato para entrega'
                }
            ]
            
            # Verificar e adicionar cada coluna
            for column in columns_to_add:
                print(f"Verificando coluna '{column['name']}'...")
                
                # Verificar se a coluna existe
                check_column = db.session.execute(text(
                    f"SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                    f"WHERE table_name='resgate' AND column_name='{column['name']}')"
                )).scalar()
                
                if not check_column:
                    print(f"  → Adicionando coluna '{column['name']}' ({column['description']})...")
                    db.session.execute(text(
                        f"ALTER TABLE resgate ADD COLUMN {column['name']} {column['type']}"
                    ))
                    print(f"  ✓ Coluna '{column['name']}' adicionada com sucesso!")
                else:
                    print(f"  ✓ Coluna '{column['name']}' já existe na tabela.")
            
            print("\n" + "=" * 60)
            print("Verificando estrutura atual da tabela 'resgate'...")
            
            # Verificar estrutura atual da tabela
            result = db.session.execute(text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name = 'resgate' "
                "ORDER BY ordinal_position"
            ))
            
            print("\nEstrutura atual da tabela 'resgate':")
            print("-" * 50)
            for row in result:
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                print(f"  {row[0]:<20} | {row[1]:<25} | {nullable}")
            
            # Confirmar alterações
            db.session.commit()
            print("\n" + "=" * 60)
            print("✓ Estrutura da tabela atualizada com sucesso!")
            
            # Opção para popular dados existentes
            print("\nDeseja popular dados existentes? (s/n): ", end="")
            response = input().lower().strip()
            
            if response in ['s', 'sim', 'y', 'yes']:
                print("\nPopulando dados existentes...")
                populate_existing_data()
            
            print("\n🎉 Processo concluído com sucesso!")
        
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao modificar o esquema: {str(e)}")
            print("Rollback executado. Nenhuma alteração foi salva.")

if __name__ == "__main__":
    main()
else:
    print("Execute este script com: python add_resgate_columns.py")
    print("Ou chame a função main() diretamente")