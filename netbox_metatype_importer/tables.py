from netbox.tables import NetBoxTable, columns
from .models import MetaType


class MetaTypeTable(NetBoxTable):
    pk = columns.ToggleColumn(visible=True)
    id = None

    actions = columns.ActionsColumn(actions=())

    def render_name(self, value):
        return '{}'.format(value.split('.')[0])

    class Meta(NetBoxTable.Meta):
        model = MetaType
        fields = ('pk', 'name', 'vendor', 'is_new', 'is_imported')
        default_columns = ('pk', 'name', 'vendor', 'is_imported')
