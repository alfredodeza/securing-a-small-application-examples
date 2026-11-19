from conftest import sign_in


def test_a_customer_cannot_read_another_customers_ticket(client):
    sign_in(client, "alice", "wonderland")
    assert client.get("/tickets/1").status_code == 200  # her own ticket
    assert client.get("/tickets/2").status_code == 404  # bob's ticket
