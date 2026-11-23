// v4: assemble the layered PSD from ai_draw.py layer exports, then render lighting in Photoshop.
// Every lighting pass is its own named layer; cat-only light is limited by a mask from the cat silhouette.
// Run: cli-anything-photoshop --json script run --file render_psd.jsx
(function () {
  var dir = 'C:/Users/salik/Documents/Adobe-Work/cat-pfp/v4/work/layers/';
  var files = [
    ['Background art', 'Sky', '01-background-art-sky.png', 0],
    ['Background art', 'Stars', '02-background-art-stars.png', 0],
    ['Background art', 'Moon', '03-background-art-moon.png', 1.5],
    ['Background art', 'Clouds', '04-background-art-clouds.png', 10],
    ['Background art', 'Hills', '05-background-art-hills.png', 16],
    ['', 'Bokeh', '06-bokeh.png', 5],
    ['Cat', 'Body', '07-cat-body.png', 0],
    ['Cat', 'Chest fur', '08-cat-chest-fur.png', 0],
    ['Cat', 'Ears', '09-cat-ears.png', 0],
    ['Cat', 'Head', '10-cat-head.png', 0],
    ['Cat', 'Nose & mouth', '11-cat-nose-mouth.png', 0],
    ['Cat', 'Eyes', '12-cat-eyes.png', 0],
    ['Cat', 'Whiskers', '13-cat-whiskers.png', 0]
  ];
  function c(s) { return charIDToTypeID(s); }
  function rgb(hex) { var k = new SolidColor(); k.rgb.hexValue = hex.replace('#', ''); return k; }
  function ellipse(cx, cy, rx, ry) { var p = []; for (var i = 0; i < 64; i++) { var t = i / 64 * 2 * Math.PI; p.push([cx + Math.cos(t) * rx, cy + Math.sin(t) * ry]); } return p; }
  function loadAlpha(layer) {
    doc.activeLayer = layer;
    var d = new ActionDescriptor(), r = new ActionReference(); r.putProperty(c('Chnl'), c('fsel')); d.putReference(c('null'), r);
    var r2 = new ActionReference(); r2.putEnumerated(c('Chnl'), c('Chnl'), c('Trsp')); d.putReference(c('T   '), r2);
    executeAction(c('setd'), d, DialogModes.NO);
  }
  function maskFromSelection(layer) {
    doc.activeLayer = layer;
    var d = new ActionDescriptor(); d.putClass(c('Nw  '), c('Chnl'));
    var r = new ActionReference(); r.putEnumerated(c('Chnl'), c('Chnl'), c('Msk ')); d.putReference(c('At  '), r);
    d.putEnumerated(c('Usng'), c('UsrM'), c('RvlS')); executeAction(c('Mk  '), d, DialogModes.NO);
  }
  function newLayer(name, blend, opacity) {
    var l = doc.artLayers.add(); l.name = name; l.blendMode = blend; l.opacity = opacity; return l;
  }
  function paint(layer, pts, feather, hex) {
    doc.activeLayer = layer; doc.selection.select(pts); if (feather) doc.selection.feather(feather);
    doc.selection.fill(rgb(hex)); doc.selection.deselect();
  }

  app.preferences.rulerUnits = Units.PIXELS;
  var doc = app.documents.add(2000, 2000, 72, 'cat-pfp-v4', NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
  var base = doc.artLayers[0];
  var groups = {};
  for (var i = 0; i < files.length; i++) {
    var src = app.open(new File(dir + files[i][2]));
    var dup = src.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    dup.name = files[i][1];
    if (files[i][3]) dup.applyGaussianBlur(files[i][3]);
    var g = files[i][0];
    if (g) {
      if (!groups[g]) { groups[g] = doc.layerSets.add(); groups[g].name = g; groups[g].move(dup, ElementPlacement.PLACEBEFORE); }
      dup.move(groups[g], ElementPlacement.PLACEATBEGINNING);
    }
  }
  base.remove();
  var cat = groups['Cat'];

  var tmp = cat.duplicate(); tmp = tmp.merge(); tmp.name = 'tmp alpha';

  var light = doc.layerSets.add(); light.name = 'Lighting'; light.move(cat, ElementPlacement.PLACEBEFORE);
  function lightLayer(name, blend, opacity) { var l = newLayer(name, blend, opacity); l.move(light, ElementPlacement.PLACEATEND); return l; }

  var form = lightLayer('Form shade', BlendMode.MULTIPLY, 55);
  paint(form, ellipse(250, 1900, 650, 520), 220, '#3b1c3a');
  paint(form, ellipse(730, 1080, 110, 230), 110, '#4a2a40');
  paint(form, ellipse(1500, 1700, 160, 420), 140, '#3b1c3a');
  var contact = lightLayer('Contact shadow', BlendMode.MULTIPLY, 60);
  paint(contact, ellipse(1080, 1290, 360, 90), 70, '#4a1c0c');
  var key = lightLayer('Key light', BlendMode.SOFTLIGHT, 70);
  paint(key, ellipse(980, 950, 380, 330), 220, '#ffd29a');
  var rim = lightLayer('Moon rim', BlendMode.SCREEN, 100);
  loadAlpha(tmp); doc.activeLayer = rim; doc.selection.fill(rgb('#9fd3ff'));
  loadAlpha(tmp); doc.selection.translate(-24, 22); doc.activeLayer = rim; doc.selection.clear(); doc.selection.deselect();
  rim.applyGaussianBlur(4);
  var lights = [form, contact, key, rim];
  for (var k = 0; k < lights.length; k++) { loadAlpha(tmp); maskFromSelection(lights[k]); }
  doc.selection.deselect();
  tmp.remove();

  var glow = newLayer('Moon glow', BlendMode.SCREEN, 35); paint(glow, ellipse(1560, 420, 520, 520), 260, '#7f9cff');
  var ground = newLayer('Ground fade', BlendMode.MULTIPLY, 60); paint(ground, [[-200, 1750], [2200, 1750], [2200, 2300], [-200, 2300]], 220, '#1a1236');
  var vig = newLayer('Vignette', BlendMode.MULTIPLY, 40);
  doc.activeLayer = vig; doc.selection.selectAll(); doc.selection.fill(rgb('#160f30'));
  doc.selection.select(ellipse(1000, 980, 1050, 1050)); doc.selection.feather(260); doc.selection.clear(); doc.selection.deselect();
  var grain = newLayer('Grain', BlendMode.OVERLAY, 22);
  doc.activeLayer = grain; doc.selection.selectAll(); doc.selection.fill(rgb('#808080')); doc.selection.deselect();
  grain.applyAddNoise(4, NoiseDistribution.GAUSSIAN, true);

  var out = [];
  for (var n = 0; n < doc.layers.length; n++) {
    var L = doc.layers[n], t = L.name;
    if (L.typename == 'LayerSet') { var ch = []; for (var j = 0; j < L.layers.length; j++) ch.push(L.layers[j].name); t += ' {' + ch.join(', ') + '}'; }
    out.push(t);
  }
  return out.join(' | ');
})();
