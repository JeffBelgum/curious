import pytest
import curious
import h11

@pytest.fixture
def remote_addr(request):
    return ('localhost', 12345)

@pytest.fixture
def h11_get_request(request):
    return h11.Request(
        method="GET",
        target="/", 
        headers=[("Host", "localhost")],
    )

@pytest.fixture
def h2_get_request(request):
    return h2.connection.Connection(
        method="GET",
        target="/", 
        headers=[("Host", "localhost")],
    )


def test_h11_stream(h11_get_request, remote_addr):
    stream = curious.Stream(h11_get_request, remote_addr)

    assert stream.method == curious.Method.GET
    assert stream.path == "/"
    assert stream.query == {}

# def test_h2_stream(h2_get_request, remote_addr):
#     stream = curious.Stream(h2_get_request, remote_addr)
# 
#     assert stream.method == curious.Method.GET
#     assert stream.path == "/"
#     assert stream.query == {}
