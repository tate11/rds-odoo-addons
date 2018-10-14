odoo.define('web_flaggrid.FlagGridView', function (require) {
"use strict";

var AbstractView = require('web.AbstractView');
var core = require('web.core');
var FlagGridModel = require('web_flaggrid.FlagGridModel');
var FlagGridController = require('web_flaggrid.FlagGridController');
var FlagGridRenderer = require('web_flaggrid.FlagGridRenderer');
var viewRegistry = require('web.view_registry');

var _lt = core._lt;

var FlagGridView = AbstractView.extend({
    display_name: _lt('FlagGrid'),
    icon: 'fa-flag',
    config: {
        Model: FlagGridModel,
        Controller: FlagGridController,
        Renderer: FlagGridRenderer,
    },
    init: function (viewInfo, params) {
        var self = this;
        this._super.apply(this, arguments);
        var arch = viewInfo.arch;
        var fields = viewInfo.fields;
        var rowFields = [];
        var sectionField, colField, cellField, ranges, cellWidget;
        _.each(arch.children, function (child) {
            if (child.tag === 'field') {
                if (child.attrs.type === 'row') {
                    if (child.attrs.section === '1' && !sectionField) {
                        sectionField = child.attrs.name;
                    }
                    rowFields.push(child.attrs.name);
                }
                if (child.attrs.type === 'col') {
                    colField = child.attrs.name;
                    ranges = _.pluck(child.children, 'attrs');
                }
                if (child.attrs.type === 'measure') {
                    cellField = child.attrs.name;
                    cellWidget = child.attrs.widget;
                }
            }
        });


        // model
        this.loadParams.ranges = ranges;
        var contextRangeName = params.context.grid_range;
        var contextRange = contextRangeName && _.findWhere(ranges, {name: contextRangeName});
        this.loadParams.currentRange = contextRange || ranges[0];
        this.loadParams.rowFields = rowFields;
        this.loadParams.sectionField = sectionField;
        this.loadParams.colField = colField;
        this.loadParams.cellField = cellField;

        // renderer
        this.rendererParams.canCreate = this.controllerParams.activeActions.create;
        this.rendererParams.fields = fields;
        this.rendererParams.noContentHelper = _.find(arch.children, function (c) {
            return c.tag === 'empty';
        });
        this.rendererParams.editableCells = this.controllerParams.activeActions.edit && arch.attrs.adjustment;
        this.rendererParams.cellWidget = cellWidget;

        // controller
        this.controllerParams.formViewID = false;
        this.controllerParams.listViewID = false;
        _.each(params.views, function (view) {
            if (view[1] === 'form') {
                self.controllerParams.formViewID = view[0];
            }
            if (view[1] === 'list') {
                self.controllerParams.listViewID = view[0];
            }
        });
        this.controllerParams.context = params.context;
        this.controllerParams.ranges = ranges;
        this.controllerParams.currentRange = this.loadParams.currentRange.name;
        this.controllerParams.navigationButtons = arch.children
            .filter(function (c) { return c.tag === 'button'; })
            .map(function (c) { return c.attrs; });
        this.controllerParams.adjustment = arch.attrs.adjustment;
        this.controllerParams.adjustName = arch.attrs.adjust_name;
    },

});

viewRegistry.add('flaggrid', FlagGridView);

return FlagGridView;
});
