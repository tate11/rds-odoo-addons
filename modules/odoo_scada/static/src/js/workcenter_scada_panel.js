odoo.define('odoo_scada.scada_panel', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');

var QWeb = core.qweb;
var _t = core._t;


var ScadaPanel = AbstractAction.extend({
    events: {
        'click #o_scada_back': 'go_back'
    },

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.context = action.context;
        this.data = action.data;
    },

    start: function () {
        var self = this;
        self.$el.html(QWeb.render("MrpWorkcenterScadaPanel", {widget: self.data}));

        return this._super.apply(this, arguments);
    },

    go_back: function(e) {
        self = this
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'mrp.workorder',
            views: [[false, 'form']],
            res_id: self.data.id
        });
    }
});

core.action_registry.add('workcenter_scada_panel', ScadaPanel);

return ScadaPanel;

});
