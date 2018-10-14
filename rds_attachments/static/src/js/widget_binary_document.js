odoo.define('rds_attachments.widget_binary_document', function(require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var basic_fields = require('web.basic_fields');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var time = require('web.time');
    var utils = require('web.utils');
    var relational_fields = require('web.relational_fields');

    var FieldBinaryFile = basic_fields.FieldBinaryFile;  
    var FieldMany2ManyTags  = relational_fields.FieldMany2ManyTags;
    var FormFieldMany2ManyTags = relational_fields.FormFieldMany2ManyTags;

    var _t = core._t;
    var qweb = core.qweb;

    var FieldDocumentViewer = FieldBinaryFile.extend({
        supportedFieldTypes: ['binary'],
        template: 'FieldDocumentViewer',
        events: {
            'click .o_docviewer_image': '_onFullscreenClick',
            'click .dv_btn_expand': '_onFullscreenClickBtn'
        },
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this.filename_value = this.recordData[this.attrs.filename];
            this.for_filename = this.recordData[this.attrs.forname];
            this.for = this.attrs.for;
            this.pwtype = this.recordData[this.attrs.pwtype];
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        
        /**
         * @private
         * @param {DOMElement} iframe
         */
        _disableButtons: function (iframe) {
            if (this.mode === 'readonly') {
                $(iframe).contents().find('button#download').hide();
            }
            $(iframe).contents().find('button#openFile').hide();
        },

        /**
         * @private
         * @returns {string} the pdf viewer URI
         */
        _getURI: function (pwtype) {
            

            if (pwtype == 'video-d') {
                var url = '/web/content/' + this.model + '/' + this.res_id + '/' + this.for + '/preview'
            } else if (pwtype == 'image') {
                var url = '/web/image/' + this.model + '/' + this.res_id + '/' + this.for + '/preview'
            } else if ((pwtype == 'pdf-d') || (pwtype == '3d-d')) {
                var url = '/web/content/' + this.model + '/' + this.res_id + '/' + this.for + '/preview';
            } else {
                var url = '/web/content/' + this.model + '/' + this.res_id + '/' + this.name + '/preview';
            }


            if ((pwtype == 'pdf') || (pwtype == 'pdf-d')) {
                return '/rds_attachments/static/libs/ViewerJS/index.html#../../../..' + url + '.pdf';
            } else if ((pwtype == '3d') || (pwtype == '3d-d')) {
                return 'rds_attachments/static/libs/Viewer3D/index.html?file=' + url + '.stl';
            } else {
                return url;
            }
        },   
        
        /**
         * @private
         * @override
         */
        _render: function () {
            var self = this;
            var $wrapper = this.$('.o_docviewer_wrapper')

            if (['pdf', 'pdf-d', '3d', '3d-d'].indexOf(self.pwtype) != -1) {
                var $iframe = this.$('.o_docviewer_frame').removeClass('o_invisible_modifier');
                $iframe.attr('src', (self._getURI(self.pwtype)) );
                
                if (['3d', '3d-d'].indexOf(self.pwtype) != -1)
                    var $controls = this.$('.dv_btn_expand').removeClass('o_invisible_modifier');

            } else if (self.pwtype == 'image') {
                var $image = this.$('.o_docviewer_image').removeClass('o_invisible_modifier');
                $image.attr("src", self._getURI(self.pwtype))

            } else if (self.pwtype == 'video-d') {
                var $video = this.$('.o_docviewer_video').removeClass('o_invisible_modifier');
                $video.find( "source" ).attr("src", self._getURI(self.pwtype))
            }

        },
        
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        _onFullscreenClick: function (e) {
            e.stopPropagation();
            var $wrapper = this.$('.o_docviewer_wrapper').toggleClass('dv_modal')
            var $image = this.$('.o_docviewer_image')
            if ($wrapper.hasClass('dv_modal')) {
                $image.css('margin-top', (0.5*$wrapper.height() - 0.5*$image.height()).toString() + 'px')
            } else {
                $image.css('margin-top', '20px')
            }
        },
        
        _onFullscreenClickBtn: function (e) {
            e.stopPropagation();
            var $wrapper = this.$('.o_docviewer_wrapper').toggleClass('dv_modal')
        }, 

        /**
         * @override
         * @private
         * @param {Event} ev
         */
        on_file_change: function (ev) {
            this._super.apply(this, arguments);
            if (this.PDFViewerApplication) {
                var files = ev.target.files;
                if (!files || files.length === 0) {
                  return;
                }
                var file = files[0];
                // TOCheck: is there requirement to fallback on FileReader if browser don't support URL
                this.PDFViewerApplication.open(URL.createObjectURL(file), 0);
            }
        },
        /**
         * Remove the behaviour of on_save_as in FieldBinaryFile.
         *
         * @override
         * @private
         * @param {MouseEvent} ev
         */
        on_save_as: function (ev) {
            ev.stopPropagation();
        },
    
    });

    var FormFieldMany2ManyTagsLink = FormFieldMany2ManyTags.extend({

        events: _.extend({}, FieldMany2ManyTags.prototype.events, {
            'mousedown .badge': '_onColorPickerMousedown',
            'click .badge': '_onColorPickerMouseup',
            'mousedown .o_colorpicker a': '_onUpdateColor',
            'focusout .o_colorpicker': '_onCloseColorPicker',
        }),


        /**
         * @private
         * @param {MouseEvent} event
         */
        _onColorPickerMousedown: function (event) {
            var self = this;
            if (this.attrs.options.no_color_change) {
                this.pickerMousedown = setTimeout(function() { return }, 300);
            } else {
                this.pickerMousedown = setTimeout(function() { self._onOpenColorPicker(event) }, 300);
            }
        },
        
        /**
         * @private
         * @param {MouseEvent} event
         */
        _onColorPickerMouseup: function (event) {
            var self = this;

            if ((this.el.className).indexOf("o_input") != -1) {
                return 
            }

            var id = $(event.currentTarget).data('id');
            var model = _.findWhere(self.value.data, {res_id: id}).model
            this.ref_field = this.attrs.options.ref_field

            if (this.pickerMousedown) {
                clearTimeout(this.pickerMousedown);
                if (this.ref_field) {
                    this._rpc({
                        model: model,
                        method: 'search_read',
                        domain: [['id', '=', id]],
                        fields: [self.ref_field],
                        limit: 1,}).then(function (res) {
                            var resource = res[0].name.split(",")
                            self.do_action({
                                type: 'ir.actions.act_window',
                                view_type: 'form',
                                view_mode: 'form',
                                res_model: resource[0],
                                views: [[false, 'form']],
                                res_id: parseInt(resource[1]),
                            })
                        });
                } else {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        view_type: 'form',
                        view_mode: 'form',
                        res_model: model,
                        views: [[false, 'form']],
                        res_id: parseInt(id),
                    })
                }
            }
        },        

        /**
         * @private
         * @param {MouseEvent} event
         */
        _onOpenColorPicker: function (event) {
            this.pickerMousedown = false
            var tag_id = $(event.currentTarget).data('id');
            var tag = _.findWhere(this.value.data, { res_id: tag_id });
            if (tag && this.colorField in tag.data) { // if there is a color field on the related model
                this.$color_picker = $(qweb.render('FieldMany2ManyTag.colorpicker', {
                    'widget': this,
                    'tag_id': tag_id,
                }));
    
                $(event.currentTarget).append(this.$color_picker);
                this.$color_picker.dropdown('toggle');
                this.$color_picker.attr("tabindex", 1).focus();
            }
        },
    });
    
    var KanbanFieldMany2ManyTagsLink = FieldMany2ManyTags.extend({
        // Remove event handlers on this widget to ensure that the kanban 'global
        // click' opens the clicked record, even if the click is done on a tag
        // This is necessary because of the weird 'global click' logic in
        // KanbanRecord, which should definitely be cleaned.
        // Anyway, those handlers are only necessary in Form and List views, so we
        // can removed them here.
        events: AbstractField.prototype.events,

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @override
         * @private
         */
        _render: function () {
            var self = this;
            this.$el.empty().addClass('o_field_many2manytags_link o_kanban_tags_link');
            _.each(this.value.data, function (m2m) {

                $('<span>', {
                    class: 'o_tag_link o_tag_color_' + (m2m.data[self.colorField] || 0),
                    text: m2m.data.display_name,
                })
                .appendTo(self.$el);
            });
        },
    });


    field_registry
        .add('document_viewer', FieldDocumentViewer)
        .add('form.many2many_tags_link', FormFieldMany2ManyTagsLink)
        .add('kanban.many2many_tags_link', KanbanFieldMany2ManyTagsLink);

});