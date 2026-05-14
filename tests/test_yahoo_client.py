from app.data.yahoo_client import YahooFinanceClient


def test_yahoo_symbol_defaults_to_nse_suffix() -> None:
    client = YahooFinanceClient()
    assert client.yahoo_symbol("RELIANCE") == "RELIANCE.NS"
    assert client.yahoo_symbol("TCS.NS") == "TCS.NS"
    assert client.yahoo_symbol("^NSEI") == "^NSEI"

