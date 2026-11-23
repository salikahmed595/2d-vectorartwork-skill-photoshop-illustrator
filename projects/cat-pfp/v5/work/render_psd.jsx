// v5: assemble the layered PSD from ai_draw.py layer exports, then render light, glow and depth in Photoshop.
// Every pass is its own named layer; character light is limited by a mask from the cat silhouette.
// Run: cli-anything-photoshop --json script run --file render_psd.jsx
(function () {
  var dir = 'C:/Users/salik/Documents/Adobe-Work/cat-pfp/v5/work/layers/';
  var files = [
    ['Background art', 'Sky', '01-background-art-sky.png', 0],
    ['Background art', 'Stars', '02-background-art-stars.png', 0],
    ['Background art', 'Moon', '03-background-art-moon.png', 1],
    ['Background art', 'Far castle', '04-background-art-far-castle.png', 7],
    ['Background art', 'Mid trees', '05-background-art-mid-trees.png', 16],
    ['Magic', 'Rune circle', '06-magic-rune-circle.png', 0],
    ['Cat', 'Cowl', '07-cat-cowl.png', 0],
    ['Cat', 'Chest fluff', '08-cat-chest-fluff.png', 0],
    ['Cat', 'Cloak', '09-cat-cloak.png', 0],
    ['Cat', 'Amulet', '10-cat-amulet.png', 0],
    ['Cat', 'Ears', '11-cat-ears.png', 0],
    ['Cat', 'Head', '12-cat-head.png', 0],
    ['Cat', 'Eyes', '13-cat-eyes.png', 0],
    ['Cat', 'Nose & mouth', '14-cat-nose-mouth.png', 0],
    ['Cat', 'Whiskers', '15-cat-whiskers.png', 0],
    ['Cat', 'Paw & orb', '16-cat-paw-orb.png', 0],
    ['Near frame', 'Wisteria', '17-near-frame-wisteria.png', 2.5],
    ['FX', 'Particles', '18-fx-particles.png', 0]
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
  var doc = app.documents.add(2000, 2000, 72, 'cat-pfp-v5', NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
  var base = doc.artLayers[0];
  var groups = {}, L = {};
  for (var i = 0; i < files.length; i++) {
    var src = app.open(new File(dir + files[i][2]));
    var dup = src.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    dup.name = files[i][1];
    if (files[i][3]) dup.applyGaussianBlur(files[i][3]);
    var g = files[i][0];
    if (!groups[g]) { groups[g] = doc.layerSets.add(); groups[g].name = g; groups[g].move(dup, ElementPlacement.PLACEBEFORE); }
    dup.move(groups[g], ElementPlacement.PLACEATBEGINNING);
    L[files[i][1]] = dup;
  }
  base.remove();
  var cat = groups['Cat'];

  // --- atmosphere inside the background ---
  var sky = L['Sky']; sky.applyGaussianBlur(30);
  var mist = newLayer('Ground mist', BlendMode.SCREEN, 45); mist.move(groups['Background art'], ElementPlacement.PLACEATBEGINNING);
  paint(mist, ellipse(1000, 1760, 1250, 330), 220, '#7a58c0');
  var mglow = newLayer('Moon glow', BlendMode.SCREEN, 45); mglow.move(L['Moon'], ElementPlacement.PLACEBEFORE);
  paint(mglow, ellipse(1690, 360, 470, 470), 260, '#8f88ff');

  // --- rune circle glow ---
  var rune = L['Rune circle'];
  var rg = rune.duplicate(); rg.name = 'Rune glow'; rg.blendMode = BlendMode.SCREEN; rg.opacity = 100; rg.applyGaussianBlur(12);
  var rb = rune.duplicate(); rb.name = 'Rune bloom'; rb.blendMode = BlendMode.SCREEN; rb.opacity = 80; rb.applyGaussianBlur(48);
  var halo = newLayer('Circle halo', BlendMode.SCREEN, 40); halo.move(groups['Magic'], ElementPlacement.PLACEATEND);
  paint(halo, ellipse(1000, 760, 640, 640), 300, '#3a6fd8');

  // --- cat silhouette alpha ---
  var tmp = cat.duplicate(); tmp = tmp.merge(); tmp.name = 'tmp alpha';

  var light = doc.layerSets.add(); light.name = 'Lighting'; light.move(cat, ElementPlacement.PLACEBEFORE);
  function lightLayer(name, blend, opacity) { var l = newLayer(name, blend, opacity); l.move(light, ElementPlacement.PLACEATEND); return l; }

  var form = lightLayer('Form shade', BlendMode.MULTIPLY, 55);
  paint(form, ellipse(1720, 1700, 520, 760), 260, '#2a1848');
  paint(form, ellipse(1000, 2180, 1100, 420), 260, '#1a1238');
  var contact = lightLayer('Contact shadow', BlendMode.MULTIPLY, 55);
  paint(contact, ellipse(1000, 1112, 300, 46), 40, '#3a1530');
  var key = lightLayer('Key light', BlendMode.SOFTLIGHT, 65);
  paint(key, ellipse(880, 760, 430, 390), 220, '#ffd8a0');
  var under = lightLayer('Magic under-light', BlendMode.SCREEN, 22);
  paint(under, ellipse(1000, 1180, 300, 160), 120, '#4fe6ff');
  paint(under, ellipse(690, 1420, 260, 220), 120, '#4fe6ff');
  var rim = lightLayer('Rune rim', BlendMode.SCREEN, 90);
  loadAlpha(tmp); doc.activeLayer = rim; doc.selection.fill(rgb('#7ff6ff'));
  loadAlpha(tmp); doc.selection.contract(9); doc.activeLayer = rim; doc.selection.clear(); doc.selection.deselect();
  rim.applyGaussianBlur(3);
  var moonrim = lightLayer('Moon rim', BlendMode.SCREEN, 60);
  loadAlpha(tmp); doc.activeLayer = moonrim; doc.selection.fill(rgb('#d9d4ff'));
  loadAlpha(tmp); doc.selection.translate(-11, 8); doc.activeLayer = moonrim; doc.selection.clear(); doc.selection.deselect();
  moonrim.applyGaussianBlur(5);
  var lights = [form, contact, key, under, rim, moonrim];
  for (var k = 0; k < lights.length; k++) { loadAlpha(tmp); maskFromSelection(lights[k]); }
  doc.selection.deselect();
  tmp.remove();

  // --- glow, grade, finish (above everything) ---
  var fxg = groups['FX'];
  function topLayer(name, blend, opacity) { var l = newLayer(name, blend, opacity); l.move(fxg, ElementPlacement.PLACEBEFORE); return l; }
  var glow = topLayer('Magic glow', BlendMode.SCREEN, 50);
  paint(glow, ellipse(1000, 1230, 210, 210), 140, '#46d8ff');
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
