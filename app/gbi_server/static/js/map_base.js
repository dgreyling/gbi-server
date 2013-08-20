var ro_symbolizer = {
    "Polygon": {
        strokeWidth: 1,
        strokeOpacity: 0.5,
        strokeColor: "#D6311E",
        fillColor: "#D6311E",
        fillOpacity: 0.5
    }
};

var rw_symbolizer = {
    "Polygon": {
        strokeWidth: 1,
        strokeOpacity: 0.5,
        strokeColor: "blue",
        fillColor: "blue",
        fillOpacity: 0.4
    }
};

var select_symbolizer = {
    strokeColor: "black",
    strokeWidth: 2,
    strokeOpacity: 1
};

var ro_style = new OpenLayers.Style();
ro_style.addRules([
    new OpenLayers.Rule({symbolizer: ro_symbolizer})
]);
var ro_style_map = new OpenLayers.StyleMap({
    "default": ro_style,
    "select": select_symbolizer
});
var rw_style = new OpenLayers.Style();
rw_style.addRules([
    new OpenLayers.Rule({symbolizer: rw_symbolizer})
]);
var rw_style_map = new OpenLayers.StyleMap({
    "default": rw_style,
    "select": select_symbolizer
});
