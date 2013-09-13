var attributeEditorLabel = {
    'noAttributes': OpenLayers.i18n('No attributes'),
    'sameKeyDifferentValue': OpenLayers.i18n('Different values for same attribute')
}

gbi.widgets = gbi.widgets || {};

gbi.widgets.AttributeEditor = function(editor, options) {
    var self = this;
    var defaults = {
        element: 'attributeeditor',
        allowNewAttributes: true
    };
    this.layerManager = editor.layerManager;
    this.options = $.extend({}, defaults, options);
    this.element = $('#' + this.options.element);
    this.selectedFeatures = [];
    this.featureChanges = {};
    this.changed = false;
    this.labelValue = undefined;
    this.renderAttributes = false;

    $.alpaca.registerView(gbi.widgets.AttributeEditor.alpacaViews.edit)
    $.alpaca.registerView(gbi.widgets.AttributeEditor.alpacaViews.display)

    this.registerEvents();

    $(gbi).on('gbi.layermanager.layer.add', function(event, layer) {
       self.registerEvents();
    });
};

gbi.widgets.AttributeEditor.prototype = {
    CLASS_NAME: 'gbi.widgets.AttributeEditor',

    registerEvents: function() {
        var self = this;
        $.each(self.layerManager.vectorLayers, function(idx, layer) {
            layer.registerEvent('featureselected', self, function(f) {
                if(!(f.feature.id in self.featureChanges)) {
                    self.featureChanges[f.feature.id] = {'added': {}, 'edited': {}, 'removed': []};
                }
                self.selectedFeatures.push(f.feature);
                self.render();
            });
            layer.registerEvent('featureunselected', self, function(f) {
                var idx = $.inArray(f.feature, self.selectedFeatures);
                if(idx != -1) {
                    self.selectedFeatures.splice(idx, 1);
                    self.render();
                }
            });
        });
    },
    render: function() {
        var self = this;
        var activeLayer = this.layerManager.active();
        var attributes = activeLayer.schemaAttributes() || [];//this.renderAttributes || activeLayer.featuresAttributes();
        var selectedFeatureAttributes = {};
        var editable = true;

        $.each(self.selectedFeatures, function(idx, feature) {
            if(feature.layer.id != activeLayer.olLayer.id) {
                editable = false;
            }
        });

        this.element.empty();
        if(this.selectedFeatures.length > 0) {
            var schemaOptions = {"fields": {}};
            $.each(activeLayer.jsonSchema.properties, function(name, prop) {
                schemaOptions.fields[name] = {
                    'id': name,
                    'readonly': !editable
                };
            });

            var data = {};
            $.each(this.selectedFeatures, function(idx, feature) {
                $.each(feature.attributes, function(key, value) {
                    //check for different values for same attribute
                    if(key in data && data[key] != value) {
                        data[key] = undefined;
                        schemaOptions.fields[key]['placeholder'] = attributeEditorLabel.sameKeyDifferentValue;
                    } else {
                        data[key] = value;
                    }
                })
            });

            this.element.append(tmpl(gbi.widgets.AttributeEditor.template))

            $.alpaca('alpaca_form', {
                schema: activeLayer.jsonSchema,
                data: data,
                options: schemaOptions,
                view: editable ? 'VIEW_GBI_EDIT' : 'VIEW_GBI_DISPLAY'
            });

            //bind events
            $.each(attributes, function(idx, key) {
                $('#'+key).change(function() {
                    var newVal = $('#'+key).val();
                    self.edit(key, newVal);
                });
                $('#_'+key+'_label').click(function() {
                    self.label(key);
                    return false;
                });
                if(editable) {
                    $('#_'+key+'_remove').click(function() {
                        self.remove(key);
                        return false;
                    });
                } else {
                    $('#_'+key+'_remove').attr('disabled', 'disabled');
                }
            });
        }
    },
    edit: function(key, value) {
        var self = this;
        $.each(this.selectedFeatures, function(idx, feature) {
            self.featureChanges[feature.id]['edited'][key] = value;
        });
        this.changed = true;
        this._applyAttributes();
        this.render();
    },
    label: function(key) {
        var symbolizers;
        if(this.labelValue == key) {
            symbolizers = {};
            $('#_' + key + '_label i')
                .removeClass('icon-eye-close')
                .addClass('icon-eye-open');
            this.labelValue = undefined;
        } else {
            var symbol = {'label': key + ': ${' + key + '}'};
            var symbolizers = {
                'Polygon': symbol
            };
            $('.add-label-button i')
                .removeClass('icon-eye-close')
                .addClass('icon-eye-open');
            $('#_' + key + '_label i')
                .removeClass('icon-eye-open')
                .addClass('icon-eye-close');
            this.labelValue = key;
        }
        this.layerManager.active().setStyle(symbolizers, true)
    },
    remove: function(key) {
        var self = this;
        $.each(this.selectedFeatures, function(idx, feature) {
            if($.inArray(key, self.featureChanges[feature.id]['removed']) == -1) {
                self.featureChanges[feature.id]['removed'].push(key);
            }
        });
        this.changed = true;
        this._applyAttributes();
        this.render();
    },
    setAttributes: function(attributes) {
        this.renderAttributes = attributes;
        this.render();
    },
    _applyAttributes: function() {
        var self = this;
        var activeLayer = this.layerManager.active();
        $.each($.extend(true, {}, this.featureChanges), function(featureId, changeSet) {
            var feature = activeLayer.featureById(featureId);
            if (feature) {
                // remove
                $.each(changeSet['removed'], function(idx, key) {
                    activeLayer.removeFeatureAttribute(feature, key);
                });
                self.featureChanges[feature.id]['removed'] = [];
                // edit
                $.each(changeSet['edited'], function(key, value) {
                    activeLayer.changeFeatureAttribute(feature, key, value);
                });
                self.featureChanges[feature.id]['edited'] = {};
                // add
                $.each(changeSet['added'], function(key, value) {
                    activeLayer.changeFeatureAttribute(feature, key, value)
                });
                self.featureChanges[feature.id]['added'] = {};

                // remove not selected features
                if($.inArray(feature, self.selectedFeatures) == -1) {
                    delete self.featureChanges[featureId];
                }
            }
        });
    },
};

gbi.widgets.AttributeEditor.template = '\
<div id="alpaca_form"></div>\
';

gbi.widgets.AttributeEditor.alpacaViews = {
    "edit": {
        "id": "VIEW_GBI_EDIT",
        "parent": "VIEW_BOOTSTRAP_EDIT",
        "templates": {
            "controlFieldContainer": "\
            <div>\
                {{html this.html}}\
                <button id='_${id}_label' title='label' class='btn btn-small add-label-button'>\
                    <i class='icon-eye-open'></i>\
                </button>\
                <button id='_${id}_remove' title='remove' class='btn btn-small'>\
                    <i class='icon-trash'></i>\
                </button>\
            </div>"
        }
    },
    "display": {
        "id": "VIEW_GBI_DISPLAY",
        "parent": "VIEW_GBI_EDIT",
        "templates": {
            "fieldSetItemContainer": '<div class="alpaca-inline-item-container control-group"></div>',
            "controlField": "\
                <div>\
                    {{html Alpaca.fieldTemplate(this,'controlFieldLabel')}}\
                    {{wrap(null, {}) Alpaca.fieldTemplate(this,'controlFieldContainer',true)}}\
                        {{html Alpaca.fieldTemplate(this,'controlFieldHelper')}}\
                    {{/wrap}}\
                </div>\
            "
        }
    }
};
