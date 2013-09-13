require("../../micro.templating.js");

var layerManagerLabel = {
    'activeLayer': OpenLayers.i18n("activeLayer"),
    'background': OpenLayers.i18n("backgroundLayerTitle"),
    'raster': OpenLayers.i18n("rasterLayerTitle"),
    'vector': OpenLayers.i18n("vectorLayerTitle"),
    'noActiveLayer': OpenLayers.i18n("noActiveLayer")
}

gbi.widgets = gbi.widgets || {};

gbi.widgets.LayerManager = function(editor, options) {
    var self = this;
    var defaults = {
        showActiveLayer: true
    };

    this.editor = editor;
    this.layerManager = editor.layerManager;
    this.options = $.extend({}, defaults, options);


    this.element = $('<div></div>');
    this.element.addClass('gbi_widgets_LayerManager');

    // add active layer
    if(this.options.showActiveLayer) {
        this.activeLayerDIV = $('<div id="layermanager_active_layer" class="label label-success">'+layerManagerLabel.activeLayer+': <span></span></div>');
        $('.olMapViewport').append(this.activeLayerDIV);
    }

    this.render();

    $('.olMapViewport').append(this.element);

    $(gbi).on('gbi.layermanager.layer.remove', function(event, layer) {
         self.render();
    });

    $(gbi).on('gbi.layermanager.layer.add', function(event, layer) {
         self.render();
    });

    $(gbi).on('gbi.layermanager.layer.active', function(event, layer) {
        if (layer === undefined) {
            $('#layermanager_active_layer > span').html(layerManagerLabel.noActiveLayer);
        }
    });
};
gbi.widgets.LayerManager.prototype = {
    render: function(accordion) {
        var self = this;
        this.element.empty();
        var layers = [];
        var rasterLayers = [];
        var backgroundLayers = [];
        var vectorLayers = [];

        $.each(this.layerManager.layers(), function(idx, gbiLayer) {
            if(gbiLayer.options.displayInLayerSwitcher) {
                if (gbiLayer.isVector) {
                    vectorLayers.push(gbiLayer);
                    if (gbiLayer.isActive) {
                        if (self.options.showActiveLayer) {
                            $('#layermanager_active_layer > span').html(gbiLayer.options.name);
                        }
                    }
                }
                if (gbiLayer.isRaster && gbiLayer.isBackground) {
                    backgroundLayers.push(gbiLayer);
                }

                if (gbiLayer.isRaster && !gbiLayer.isBackground) {
                    rasterLayers.push(gbiLayer);
                }
                layers.push(gbiLayer);
            }
        });
        if (!this.layerManager.active()) {
            $('#layermanager_active_layer > span').html(layerManagerLabel.noActiveLayer);
        }

        if (!accordion) {
            accordion = 'collapseVector';
        }

        this.element.append(tmpl(gbi.widgets.LayerManager.template, {
            backgroundLayers: backgroundLayers,
            rasterLayers: rasterLayers,
            vectorLayers: vectorLayers,
            accordion: accordion,
            self: this}));

        //bind events
        $.each(layers, function(idx, layer) {
            self.element.find('#visible_' + layer.id)
                .prop('checked', layer.visible())
                .click(function(e) {
                    var status = $(this).prop("checked");
                    layer.visible(status);
                    e.stopPropagation()
                });
        });

        this.element.find('.gbi_widgets_LayerManager_LayerSwitcher')
            .click(function(event) {
                event.stopPropagation();
            })
            .dblclick(function(event) {
                event.stopPropagation();
            }).mousedown(function(event) {
                event.stopPropagation();
            });

        this.element.find('.gbi_widgets_LayerManager_Minimize').click(function(event) {
            event.stopPropagation();
            self.element.find('.gbi_widgets_LayerManager_LayerSwitcher').hide();
            self.element.find('.gbi_widgets_LayerManager_Minimize').hide();
            self.element.find('.gbi_widgets_LayerManager_Maximize').show();
        }).dblclick(function(event) {
            event.stopPropagation();
        }).show();
        this.element.find('.gbi_widgets_LayerManager_Maximize').click(function(event) {
            event.stopPropagation();
            self.element.find('.gbi_widgets_LayerManager_LayerSwitcher').show();
            self.element.find('.gbi_widgets_LayerManager_Minimize').show();
            self.element.find('.gbi_widgets_LayerManager_Maximize').hide();
        }).dblclick(function(event) {
            event.stopPropagation();
        }).hide();

    },
    findAccordion: function(element) {
       var accordion = $(element).closest('.accordion-body ');
       return $(accordion).attr('id');
    }
};

gbi.widgets.LayerManager.template = '\
    <div class="gbi_widgets_LayerManager_Maximize"></div>\
    <div class="gbi_widgets_LayerManager_Minimize"></div>\
    <div class="gbi_widgets_LayerManager_LayerSwitcher">\
        <h5>'+layerManagerLabel.background+'\</h5>\
        <ul>\
            <% for(var i=0; i<backgroundLayers.length; i++) { %>\
                <li class="gbi_layer">\
                    <input type="checkbox" id="visible_<%=backgroundLayers[i].id%>" />\
                    <span><%=backgroundLayers[i].options.label%></span>\
                </li>\
            <% } %>\
        </ul>\
        <% if(rasterLayers.length != 0) { %> \
            <h5>'+layerManagerLabel.raster+'\</h5>\
            <ul>\
                <% for(var i=0; i<rasterLayers.length; i++) { %>\
                    <li class="gbi_layer">\
                        <input type="checkbox" id="visible_<%=rasterLayers[i].id%>" />\
                        <span><%=rasterLayers[i].options.label%></span>\
                    </li>\
                <% } %>\
            </ul>\
            <% } %> \
        <% if(vectorLayers.length != 0) { %> \
            <h5>'+layerManagerLabel.vector+'\</h5>\
            <ul>\
                <% for(var i=0; i<vectorLayers.length; i++) { %>\
                    <li class="gbi_layer">\
                        <input type="checkbox" id="visible_<%=vectorLayers[i].id%>" />\
                        <span><%=vectorLayers[i].olLayer.name%></span>\
                    </li>\
                <% } %>\
            </ul>\
        <% } %> \
    </div>\
';