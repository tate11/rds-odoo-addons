odoo.define('rds_attachments.ChatThread', function (require) {
"use strict";

var Thread = require('mail.ChatThread');


Thread.include({
    _onAttachmentView: function (event) {
        var activeAttachmentID = $(event.currentTarget).data('id');
        self = this
        this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: [['id', '=', activeAttachmentID]],
            fields: ['document_id'],
            limit: 1,
        }).then(function (docid) {
            try {
                docid = docid.g[0].document_id
            } catch (err) {
                docid = false
            }
            if(docid) {
                
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: "Document",
                    res_model: 'rds.ir.document',
                    res_id: docid,
                    views: [
                        [self.formViewID, 'form']
                    ],
                    target: 'this',
                });
            } else {
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: "Document",
                    res_model: 'ir.attachment',
                    res_id: activeAttachmentID,
                    views: [
                        [self.formViewID, 'form']
                    ],
                    target: 'this',
                });
            }
        });
    },
});


});
