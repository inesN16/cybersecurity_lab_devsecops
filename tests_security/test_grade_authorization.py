import baseline_secure_coding_api as api

def login(client, username, password):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert response.get_json()["user"] == username

def test_assigned_professor_can_update_grade(client):
    login(client, "prof_srs", "profpw")
    response = client.post(
        "/grades/update",
        json={"student_id": 1001, "course_id": "SRS", "grade": 18},
    )
    assert response.status_code == 200
    assert api.find_grade(1001, "SRS")["grade"] == 18

##############################################################################



def test_alice_tenta_mudar_a_sua_nota(client):
    
    # fazer login com a conta da alice
    login(client, "alice", "alicepw")
    
    # preparar os dados para tentar dar um 20 a si mesma
    dados_ataque = {
        "student_id": 1001, 
        "course_id": "SRS", 
        "grade": 20
    }
    
    # enviar o pedido post
    res = client.post("/grades/update", json=dados_ataque)
    
    # isto tem de ser proibido (403), mas a api vulneravel vai deixar passar e dar 200
    assert res.status_code == 403
    
    # verificar se a nota na base de dados (memoria) nao foi alterada
    nota_atual = api.find_grade(1001, "SRS")
    assert nota_atual["grade"] != 20