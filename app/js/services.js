angular.module('thematicMap', []);

angular.module('thematicMap')
.service('getColor', function(){
    return function getColor(regiao){
        return regiao == 'NORDESTE'     ? '#FC4E2A' :
               regiao == 'NORTE'        ? '#009933' :
               regiao == 'SUDESTE'      ? '#E31A1C' :
               regiao == 'SUL'          ? '#0066FF' :
               regiao == 'CENTRO-OESTE' ? '#FFCC00' :
                                          '#FFEDA0';
    };
})

.service('style', function(getColor){
    return function style(feature) {
        return {
            fillColor: getColor(feature.properties.regiao),
            weight: 2,
            opacity: 1,
            color: 'black',
            dashArray: '3',
            fillOpacity: 0.7
        };
    };
})


/*
Function to highlight feature on mouseover
called on onEachFeature -> layer.on({mouseover}) 
*/
.service('highlightFeature', function(){
    return function highlightFeature(e) {
        var layer = e.target;

        layer.setStyle({
            weight: 5,
            color: 'red',
            dashArray: '',
            fillOpacity: 0.7
        });

        if (!L.Browser.ie && !L.Browser.opera) {
            layer.bringToFront();
        }
    };

})


/*
Function to highlight feature on mouseover
called on onEachFeature -> layer.on({mouseover}) 
*/
.service('resetHighlight', function(){
    return function resetHighlight(e) {
        var layer = e.target;

        layer.setStyle({
            weight: 2,
            opacity: 1,
            color: 'black',
            dashArray: '3',
            fillOpacity: 0.7
        });

        if (!L.Browser.ie && !L.Browser.opera) {
            layer.bringToFront();
        }
    };

})


;