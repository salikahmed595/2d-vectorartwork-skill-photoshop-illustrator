// v7: assemble the layered PSD from ai_draw.py layer exports, then render light and glow in Photoshop.
// Every pass is its own named layer; character light is limited by a mask from the cat silhouette.
// Changes from v6: Mist layer (vector); every background Gaussian blur removed (Sky, Moon, Far castle, Mid trees,
// Wisteria) and the feathered Ground mist dropped - depth now comes from value, scale and overlap in the vector art.
// Run: cli-anything-photoshop --json script run --file render_psd_v7.jsx
(function () {
  var dir = 'C:/Users/salik/Documents/Adobe-Work/cat-pfp/v7/work/layers_v7/';
  var files = [  // v7: no background blur on any layer (skill v3 rule 13 / user rule)
    ['Background art', 'Sky', '01-background-art-sky.png'],
    ['Background art', 'Stars', '02-background-art-stars.png'],
    ['Background art', 'Moon', '03-background-art-moon.png'],
    ['Background art', 'Far castle', '04-background-art-far-castle.png'],
    ['Background art', 'Mist', '05-background-art-mist.png'],
    ['Background art', 'Mid trees', '06-background-art-mid-trees.png'],
    ['Magic', 'Rune circle', '07-magic-rune-circle.png'],
    ['Cat', 'Cowl', '08-cat-cowl.png'],
    ['Cat', 'Chest fluff', '09-cat-chest-fluff.png'],
    ['Cat', 'Cloak', '10-cat-cloak.png'],
    ['Cat', 'Upper arm', '11-cat-upper-arm.png'],
    ['Cat', 'Cloak trim', '12-cat-cloak-trim.png'],
    ['Cat', 'Amulet', '13-cat-amulet.png'],
    ['Cat', 'Neck ruff', '14-cat-neck-ruff.png'],
    ['Cat', 'Paw & orb', '15-cat-paw-orb.png'],
    ['Cat', 'Ears', '16-cat-ears.png'],
    ['Cat', 'Head', '17-cat-head.png'],
    ['Cat', 'Eyes', '18-cat-eyes.png'],
    ['Cat', 'Nose & mouth', '19-cat-nose-mouth.png'],
    ['Cat', 'Whiskers', '20-cat-whiskers.png'],
    ['Near frame', 'Wisteria', '21-near-frame-wisteria.png'],
    ['FX', 'Particles', '22-fx-particles.png']
  ];
  function c(s) { return charIDToTypeID(s); }
  function rgb(hex) { var k = new SolidColor(); k.rgb.hexValue = hex.replace('#', ''); return k; }
  function ellipse(cx, cy, rx, ry) { var p = []; for (var i = 0; i < 72; i++) { var t = i / 72 * 2 * Math.PI; p.push([cx + Math.cos(t) * rx, cy + Math.sin(t) * ry]); } return p; }
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
  function newLayer(name, blend, opacity) { var l = doc.artLayers.add(); l.name = name; l.blendMode = blend; l.opacity = opacity; return l; }
  function paint(layer, pts, feather, hex) {
    doc.activeLayer = layer; doc.selection.select(pts); if (feather) doc.selection.feather(feather);
    doc.selection.fill(rgb(hex)); doc.selection.deselect();
  }

  app.preferences.rulerUnits = Units.PIXELS;
  var doc = app.documents.add(2000, 2000, 72, 'cat-pfp-v7', NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
  var base = doc.artLayers[0];
  var groups = {}, L = {};
  for (var i = 0; i < files.length; i++) {
    var src = app.open(new File(dir + files[i][2]));
    var dup = src.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    dup.name = files[i][1];
    var g = files[i][0];
    if (!groups[g]) { groups[g] = doc.layerSets.add(); groups[g].name = g; groups[g].move(dup, ElementPlacement.PLACEBEFORE); }
    dup.move(groups[g], ElementPlacement.PLACEATBEGINNING);
    L[files[i][1]] = dup;
  }
  base.remove();
  var cat = groups['Cat'];

  // --- atmosphere inside the background ---
  var mglow = newLayer('Moon glow', BlendMode.SCREEN, 22); mglow.move(L['Moon'], ElementPlacement.PLACEBEFORE);
  paint(mglow, ellipse(1690, 360, 440, 440), 240, '#8f88ff');

  // --- rune circle glow (D4: lower than v5 so the face stays the focal point) ---
  var rune = L['Rune circle'];
  var rg = rune.duplicate(); rg.name = 'Rune glow'; rg.blendMode = BlendMode.SCREEN; rg.opacity = 70; rg.applyGaussianBlur(10);
  var rb = rune.duplicate(); rb.name = 'Rune bloom'; rb.blendMode = BlendMode.SCREEN; rb.opacity = 50; rb.applyGaussianBlur(44);
  var halo = newLayer('Circle halo', BlendMode.SCREEN, 30); halo.move(groups['Magic'], ElementPlacement.PLACEATEND);
  paint(halo, ellipse(1000, 760, 640, 640), 300, '#3a6fd8');

  // --- cat silhouette alpha ---
  var tmp = cat.duplicate(); tmp = tmp.merge(); tmp.name = 'tmp alpha';

  var light = doc.layerSets.add(); light.name = 'Lighting'; light.move(cat, ElementPlacement.PLACEBEFORE);
  function lightLayer(name, blend, opacity) { var l = newLayer(name, blend, opacity); l.move(light, ElementPlacement.PLACEATEND); return l; }

  var form = lightLayer('Form shade', BlendMode.MULTIPLY, 55);
  paint(form, ellipse(1720, 1700, 520, 760), 260, '#2a1848');
  paint(form, ellipse(1000, 2180, 1100, 420), 260, '#1a1238');
  var key = lightLayer('Key light', BlendMode.SOFTLIGHT, 65);
  paint(key, ellipse(880, 760, 430, 390), 220, '#ffd8a0');
  var under = lightLayer('Magic under-light', BlendMode.SCREEN, 20);
  paint(under, ellipse(1000, 1200, 280, 150), 120, '#4fe6ff');
  paint(under, ellipse(690, 1440, 260, 220), 120, '#4fe6ff');
  var rim = lightLayer('Rune rim', BlendMode.SCREEN, 85);
  loadAlpha(tmp); doc.activeLayer = rim; doc.selection.fill(rgb('#7ff6ff'));
  loadAlpha(tmp); doc.selection.contract(8); doc.activeLayer = rim; doc.selection.clear(); doc.selection.deselect();
  rim.applyGaussianBlur(3);
  var moonrim = lightLayer('Moon rim', BlendMode.SCREEN, 60);
  loadAlpha(tmp); doc.activeLayer = moonrim; doc.selection.fill(rgb('#d9d4ff'));
  loadAlpha(tmp); doc.selection.translate(-11, 8); doc.activeLayer = moonrim; doc.selection.clear(); doc.selection.deselect();
  moonrim.applyGaussianBlur(5);
  var lights = [form, key, under, rim, moonrim];
  for (var k = 0; k < lights.length; k++) { loadAlpha(tmp); maskFromSelection(lights[k]); }
  doc.selection.deselect();
  tmp.remove();

  // --- glow, grade, finish (above everything) ---
  var fxg = groups['FX'];
  function topLayer(name, blend, opacity) { var l = newLayer(name, blend, opacity); l.move(fxg, ElementPlacement.PLACEBEFORE); return l; }
  var glow = topLayer('Magic glow', BlendMode.SCREEN, 50);
  paint(glow, ellipse(1000, 1230, 200, 200), 140, '#46d8ff');
  paint(glow, ellipse(670, 1440, 240, 240), 150, '#46d8ff');
  var grade = topLayer('Colour grade', BlendMode.SOFTLIGHT, 22);
  doc.activeLayer = grade; doc.selection.selectAll(); doc.selection.fill(rgb('#3a2a8a')); doc.selection.deselect();
  var vig = topLayer('Vignette', BlendMode.MULTIPLY, 45);
  doc.activeLayer = vig; doc.selection.selectAll(); doc.selection.fill(rgb('#120a2a'));
  doc.selection.select(ellipse(1000, 900, 1080, 1080)); doc.selection.feather(280); doc.selection.clear(); doc.selection.deselect();
  var grain = topLayer('Grain', BlendMode.OVERLAY, 18);
  doc.activeLayer = grain; doc.selection.selectAll(); doc.selection.fill(rgb('#808080')); doc.selection.deselect();
  grain.applyAddNoise(3.5, NoiseDistribution.GAUSSIAN, true);

  var out = [];
  for (var n = 0; n < doc.layers.length; n++) {
    var Ly = doc.layers[n], t = Ly.name;
    if (Ly.typename == 'LayerSet') { var ch = []; for (var j = 0; j < Ly.layers.length; j++) ch.push(Ly.layers[j].name); t += ' {' + ch.join(', ') + '}'; }
    out.push(t);
  }
  return out.join(' | ');
})();
