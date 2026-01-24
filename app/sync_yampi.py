import requests
import json

# Credenciais Yampi
TOKEN = "WnUywC0wcNGFWFlSn6UelW1VqNBOnnfidkczUhkw"
SECRET = "sk_shYPIoIJ6qasmxlnykpxJsROJwTU8aMZ1jzee"

headers = {
    "User-Token": TOKEN,
    "User-Secret-Key": SECRET,
    "Content-Type": "application/json"
}

# Buscar produtos
try:
    response = requests.get(
        "https://api.yampi.io/v1/catalog/products?limit=50",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        produtos = data.get('data', [])
        
        print(f"✅ {len(produtos)} produtos encontrados!\n")
        
        # Gerar SQL
        print("-- Copie este SQL e execute no servidor:\n")
        print("TRUNCATE TABLE produto_yampi CASCADE;")
        
        for i, p in enumerate(produtos, 1):
            nome = p.get('name', 'Produto').replace("'", "''")
            desc = p.get('description', '')[:200].replace("'", "''")
            sku = p.get('sku', f"SKU-{p.get('id')}")
            preco = float(p.get('price', 0))
            imagem = p.get('images', [{}])[0].get('url', '') if p.get('images') else ''
            
            sql = f"""
INSERT INTO produto_yampi (yampi_id, sku, nome, descricao, imagem_url, preco_original, percentual_desconto, diamantes_necessarios, ativo, ordem, categoria)
VALUES ('{p.get("id")}', '{sku}', '{nome}', '{desc}', '{imagem}', {preco}, 50, 1000, TRUE, {i}, 'Produtos');
"""
            print(sql)
        
        print("\n✅ SQL gerado! Copie e execute no servidor.")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Erro: {e}")
