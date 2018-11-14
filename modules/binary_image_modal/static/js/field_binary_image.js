odoo.define('binaryImageModal.FieldBinaryImage', function (require) {
"use strict";

var core = require('web.core');
var DocumentViewer = require('mail.DocumentViewer');
var basic_fields = require('web.basic_fields');
var FieldBinaryImage = basic_fields.FieldBinaryImage;

var FieldBinaryImage = FieldBinaryImage.include({
    template: 'FieldBinaryImage',

    /**
     * @override
     */
    events: _.extend({}, FieldBinaryImage.prototype.events, {
        'click img': function () {
            if ((this.mode === "readonly") & (this.field.attachment)) {
                this._onAttachmentView();
            }
        },
    }),

    _onAttachmentView: function (ev) {
        self = this
        this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: [['res_model', '=', this.model], ['res_id', '=', this.res_id], ['res_field', 'in', ['image', self.name]]],
            fields: ['id', 'name', 'res_name', 'mimetype', 'type', 'url', 'file_size'],
            limit: 2
        }).then(function (atts) {
            if (!atts.length) {
                return    
            } else if (atts.length == 2) {
                atts = atts.sort(function (el) {
                    return el.file_size
                });
            }
            

            var _att = atts[0]
            var att = [{
                "filename": _att.res_name,
                "id": _att.id,
                "​​main": true,
                "mimetype": _att.mimetype,
                "name": _att.name,
                "type": ((_att.type == 'url') ? 'url' : 'image'),
                "url": ((_att.type == 'url') ? _att.url : '/web/image/'+_att.id),
                }];
            
            var attachmentViewer = new DocumentViewer(self, att, _att.id);
            attachmentViewer.appendTo($('body'));
        });
    },
});
});

