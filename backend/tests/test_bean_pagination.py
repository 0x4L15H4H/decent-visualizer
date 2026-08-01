from pathlib import Path

from app.db import Database
from app.models.bean import BeanCreate
from app.models.entities import EntityCreate
from app.storage.beans import BeanStorage
from app.storage.entities import EntityStorage


def test_list_page_filters_sorts_and_returns_only_requested_page(tmp_path: Path):
    database = Database(str(tmp_path / "test.sqlite3"))
    entities = EntityStorage(database)
    roaster = entities.create(EntityCreate(kind="roaster", name="Sey Coffee"))
    beans = BeanStorage(database)
    beans.create(BeanCreate(name="Zulu", roaster_id=roaster.id, notes="Ethiopia washed"))
    beans.create(BeanCreate(name="Alpha", roaster_id=roaster.id, notes="Ethiopia natural"))

    result = beans.list_page(page=1, page_size=1, q="ethiopia", sort_by="name", descending=False)

    assert result.total == 2
    assert result.page == 1
    assert [bean.name for bean in result.items] == ["Alpha"]
