from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

from supabase import Client

from app.storage.beans import BeanStorage


def test_list_page_uses_full_text_rpc_and_fetches_only_the_requested_page():
    bean_id = "1e7969d6-a99a-4ca9-84c0-73995678e622"
    search_rpc = MagicMock()
    search_rpc.execute.return_value = SimpleNamespace(data=[{"id": bean_id, "total_count": 42}])

    bean_builder = MagicMock()
    bean_builder.select.return_value = bean_builder
    bean_builder.in_.return_value = bean_builder
    bean_builder.execute.return_value = SimpleNamespace(
        data=[
            {
                "id": bean_id,
                "name": "Halo Hartume",
                "roaster": {"id": "roaster-1", "name": "Sey Coffee"},
                "producer": None,
                "farm": None,
                "country_code": "ET",
                "variety": None,
                "process": {"id": "process-1", "name": "Washed"},
                "roast_level": None,
                "roast_date": None,
                "notes": "Bergamot",
                "created_at": "2026-06-28T00:00:00Z",
            }
        ]
    )

    client = MagicMock()
    builders = {
        "beans": bean_builder,
        "canonical_entities": MagicMock(),
        "entity_aliases": MagicMock(),
    }

    def table(name: str) -> MagicMock:
        return builders[name]

    client.table.side_effect = table
    client.rpc.return_value = search_rpc

    result = BeanStorage(cast(Client, client)).list_page(
        page=2,
        page_size=20,
        q="ethiopia washed",
        sort_by="name",
        descending=False,
    )

    client.rpc.assert_called_once_with(
        "search_bean_ids",
        {
            "p_query": "ethiopia washed",
            "p_offset": 20,
            "p_limit": 20,
            "p_sort_by": "name",
            "p_desc": False,
        },
    )
    bean_builder.in_.assert_called_once_with("id", [bean_id])
    assert result.total == 42
    assert result.page == 2
    assert [bean.name for bean in result.items] == ["Halo Hartume"]
