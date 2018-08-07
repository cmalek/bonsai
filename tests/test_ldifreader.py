import pytest

from io import StringIO, BytesIO
from bonsai import LDIFReader, LDIFError


def test_init_params():
    """ Test constructor parameters for LDIFReader. """
    with pytest.raises(TypeError):
        _ = LDIFReader("wrong")
    with pytest.raises(TypeError):
        _ = LDIFReader(StringIO(), max_length=None)
    with pytest.raises(TypeError):
        _ = LDIFReader(BytesIO())
    inp = StringIO()
    ldif = LDIFReader(inp, max_length=100)
    assert ldif.input_file == inp
    assert ldif.max_length == 100


def test_version():
    """ Test setting version attribute from LDIF. """
    text = "version: 1\ndn: cn=test\ncn: test\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif)
        ent = next(reader)
        assert reader.version == 1
        assert ent.dn == "cn=test"


def test_missing_dn():
    """ Test missing distinguished name in LDIF entry. """
    text = "changetype: add\nsn: test\ncn: test\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif)
        with pytest.raises(LDIFError) as err:
            _ = next(reader)
        assert "Missing distinguished name" in str(err)
        assert "entry #1" in str(err)


def test_invalid_file():
    """ Test invalid and too long line. """
    text = " invalid\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif)
        with pytest.raises(LDIFError) as err:
            _ = next(reader)
        assert "Parser error" in str(err)
    text = "dn: cn=test\nnotvalid attribute\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif)
        with pytest.raises(LDIFError) as err:
            _ = next(reader)
        assert "Invalid attribute value pair:" in str(err)
        assert "entry #1" in str(err)
    text = "dn: cn=toolong\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif, max_length=12)
        with pytest.raises(LDIFError) as err:
            _ = next(reader)
        assert "too long" in str(err)
        assert "Line 1" in str(err)
    text = "dn: cn=test notvalid: attribute\n"
    with StringIO(text) as ldif:
        reader = LDIFReader(ldif)
        with pytest.raises(LDIFError) as err:
            _ = next(reader)
        assert "Invalid attribute value pair:" in str(err)
        assert "entry #1" in str(err)


def test_comment():
    """ Test parsing comment lines in LDIF files. """
    ldif = "# DN: cn=test\ndn: cn=test\n#Other comment line.\ncn: test\n"
    with StringIO(ldif) as test:
        reader = LDIFReader(test)
        ent = next(reader)
        assert ent.dn == "cn=test"
        assert ent["cn"] == ["test"]
    multiline = "# A long multiline comment\n in an LDIF file.\ndn: cn=test\n"
    with StringIO(multiline) as test:
        reader = LDIFReader(test)
        ent = next(reader)
        assert ent.dn == "cn=test"


def test_input_file():
    """ Test input_file property. """
    inp = StringIO()
    ldif = LDIFReader(inp)
    assert ldif.input_file == inp
    with pytest.raises(TypeError):
        ldif.input_file = None
    inp2 = StringIO()
    ldif.input_file = inp2
    assert ldif.input_file == inp2


def test_autoload():
    """ Test autoload property. """
    inp = StringIO()
    ldif = LDIFReader(inp)
    assert ldif.autoload == True
    with pytest.raises(TypeError):
        ldif.autoload = "Yes"
    ldif.autoload = False
    assert ldif.autoload == False


def test_resource_handlers():
    """ Test resource_handlers property. """
    inp = StringIO()
    ldif = LDIFReader(inp)
    assert isinstance(ldif.resource_handlers, dict)
    assert "file" in ldif.resource_handlers.keys()
    with pytest.raises(ValueError):
        ldif.resource_handlers = {"New": "dict"}
    ldif.resource_handlers["http"] = lambda x: x
    assert "http" in ldif.resource_handlers.keys()


def test_multiline_attribute():
    """ Test parsing multiline attributes in LDIF. """
    text = "dn: cn=unimaginably+sn=very,ou=very,dc=very,dc=long,\n dc=line\ncn: unimaginably\nsn: very\n"
    with StringIO(text) as test:
        reader = LDIFReader(test)
        ent = next(reader)
    assert ent.dn == "cn=unimaginably+sn=very,ou=very,dc=very,dc=long,dc=line"
    assert ent["cn"][0] == "unimaginably"
    assert ent["sn"][0] == "very"


def test_multiple_entries():
    """ Test parsing multiple entries in one LDIF. """
    text = "dn: cn=test1\ncn: test1\n\ndn: cn=test2\ncn: test2\n"
    with StringIO(text) as test:
        reader = LDIFReader(test)
        entries = list(reader)
    assert len(entries) == 2
    assert entries[0].dn == "cn=test1"
    assert entries[1]["cn"][0] == "test2"


def test_changetype():
    """ Test changetype attribute in LDIF file. """
    text = "dn: cn=test\nchangetype: add\ncn: test\n"
    with StringIO(text) as test:
        reader = LDIFReader(test)
        ent = next(reader)
    assert ent.dn == "cn=test"
    assert "cn" in ent
    assert "changetype" not in ent