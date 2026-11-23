// Assemble the v3 layered PSD from the per-layer PNGs exported by ai_draw.py (manifest order = bottom to top).
// Run: cli-anything-photoshop --json script run --file build_psd.jsx
(function () {
  var dir = 'C:/Users/salik/Documents/Adobe-Work/cat-pfp/v3/work/layers/';
  var files = [
    ['Background art', 'Sky', '01-background-art-sky.png'],
    ['Background art', 'Stars', '02-background-art-stars.png'],
    ['Background art', 'Moon', '03-background-art-moon.png'],
    ['Background art', 'Clouds', '04-background-art-clouds.png'],
    ['Background art', 'Mountains', '05-background-art-mountains.png'],
    ['Cat', 'Body', '06-cat-body.png'],
    ['Cat', 'Chest fur', '07-cat-chest-fur.png'],
    ['Cat', 'Ears', '08-cat-ears.png'],
    ['Cat', 'Head', '09-cat-head.png'],
    ['Cat', 'Nose & mouth', '10-cat-nose-mouth.png'],
    ['Cat', 'Eyes', '11-cat-eyes.png'],
    ['Cat', 'Whiskers', '12-cat-whiskers.png'],
    ['', 'Fireflies', '13-fireflies.png']
  ];
  app.preferences.rulerUnits = Units.PIXELS;
  var doc = app.documents.add(2000, 2000, 72, 'cat-pfp-v3', NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
  var base = doc.artLayers[0];
  var groups = {};
  for (var i = 0; i < files.length; i++) {
    var g = files[i][0], name = files[i][1];
    var src = app.open(new File(dir + files[i][2]));
    var dup = src.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    dup.name = name;
    if (g) {
      if (!groups[g]) { groups[g] = doc.layerSets.add(); groups[g].name = g; groups[g].move(dup, ElementPlacement.PLACEBEFORE); }
      dup.move(groups[g], ElementPlacement.PLACEATBEGINNING);
    }
  }
  base.remove();
  var out = [];
  for (var k = 0; k < doc.layers.length; k++) {
    var L = doc.layers[k], s = L.name;
    if (L.typename == 'LayerSet') { var c = []; for (var j = 0; j < L.layers.length; j++) c.push(L.layers[j].name); s += ' {' + c.join(', ') + '}'; }
    out.push(s);
  }
  return out.join(' | ');
})();
