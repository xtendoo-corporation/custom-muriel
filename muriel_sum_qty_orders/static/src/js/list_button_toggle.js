odoo.define('muriel_sum_qty_orders.list_toggle', function (require) {
    "use strict";

    var ListController = require('web.ListController');

    ListController.include({
        _onSelectionChanged: function () {
            this._super.apply(this, arguments);
            try {
                var $button = this.$el.find('button.o_list_button_muriel_sum_qty');
                if ($button.length) {
                    // this.getSelectedIds is available in some Odoo versions; fallback to selectedRowIds
                    var selected = [];
                    if (this.getSelectedIds) {
                        selected = this.getSelectedIds();
                    } else if (this.selectedRowIds) {
                        selected = this.selectedRowIds;
                    }
                    if (selected && selected.length) {
                        $button.show().prop('disabled', false);
                    } else {
                        $button.hide().prop('disabled', true);
                    }
                }
            } catch (e) {
                console.error('muriel_sum_qty_orders: error toggling button', e);
            }
        },
    });
});

