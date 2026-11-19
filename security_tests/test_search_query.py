from conftest import sign_in


def test_search_words_cannot_change_the_query(client):
    sign_in(client, "alice", "wonderland")
    found = client.get("/search", query_string={"q": "' OR 1=1 --"}).get_json()
    assert found == []
    assert client.get("/search", query_string={"q": "late"}).get_json() != []
