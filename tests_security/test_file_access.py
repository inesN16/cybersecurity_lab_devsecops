import baseline_secure_coding_api as api

def test_path_traversal_blocked(client, tmp_path, monkeypatch):
    # 1. Cria uma pasta falsa para materiais e um ficheiro secreto fora dela
    fake_materials = tmp_path / "materials"
    fake_materials.mkdir()
    secret_file = tmp_path / "secret_passwords.txt"
    secret_file.write_text("SENHAS_SUPER_SECRETAS")
    
    # Engana a API para usar a nossa pasta falsa
    monkeypatch.setattr(api, "MATERIALS_DIR", fake_materials)
    
    # 2. Ataque: tenta recuar com "../" e ler o ficheiro proibido
    response = client.get("/files?path=../secret_passwords.txt")
    
    # 3. O requisito R6 diz que pedidos fora da pasta devem ser bloqueados.
    # O teste vai falhar porque a API vulnerável vai cuspir o conteúdo do ficheiro!
    assert response.status_code != 200
    assert b"SENHAS_SUPER_SECRETAS" not in response.data