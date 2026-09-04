(function () {
  function escapeXml(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderArcDiagram(container, depTokens) {
    if (!depTokens || !depTokens.length) {
      container.innerHTML = '<p class="text-muted mb-0">No dependency data.</p>';
      return;
    }

    const n = depTokens.length;
    const W = Math.max(720, n * 72);
    const H = 260;
    const margin = 36;
    const baseY = H - 56;
    const step = (W - 2 * margin) / n;
    const xs = depTokens.map(function (_, i) {
      return margin + (i + 0.5) * step;
    });

    const parts = [];
    parts.push(
      '<svg width="' +
        W +
        '" height="' +
        H +
        '" xmlns="http://www.w3.org/2000/svg" class="dependency-svg">'
    );

    depTokens.forEach(function (t, i) {
      const h = t.head_id;
      if (h === null || h === undefined) return;
      const x1 = xs[i];
      const x2 = xs[h];
      const bump = 32 + Math.abs(i - h) * 16;
      const mid = (x1 + x2) / 2;
      const yc = baseY - bump;
      const path =
        'M ' + x1 + ' ' + baseY + ' Q ' + mid + ' ' + yc + ' ' + x2 + ' ' + baseY;
      parts.push(
        '<path d="' +
          path +
          '" fill="none" stroke="#94a3b8" stroke-width="1.6" stroke-linecap="round"/>'
      );
      const lab = t.dep && t.dep !== 'root' ? t.dep : '';
      if (lab) {
        parts.push(
          '<text x="' +
            mid +
            '" y="' +
            (yc - 6) +
            '" text-anchor="middle" font-size="11" fill="#475569" font-family="system-ui,sans-serif">' +
            escapeXml(lab) +
            '</text>'
        );
      }
    });

    depTokens.forEach(function (t, i) {
      const x = xs[i];
      parts.push(
        '<text x="' +
          x +
          '" y="' +
          (baseY + 20) +
          '" text-anchor="middle" font-size="14" font-weight="600" font-family="system-ui,sans-serif" fill="#0f172a">' +
          escapeXml(t.text) +
          '</text>'
      );
      parts.push(
        '<text x="' +
          x +
          '" y="' +
          (baseY + 38) +
          '" text-anchor="middle" font-size="11" fill="#64748b" font-family="system-ui,sans-serif">' +
          escapeXml(t.pos_label || t.tag || '') +
          '</text>'
      );
    });

    parts.push('</svg>');
    container.innerHTML = parts.join('');
  }

  /**
   * Older saved analyses only have `dependencies` (1-based id/head). Convert to token rows
   * matching spaCy shape so arcs and hierarchy work without DB rebuild.
   */
  function legacyDependenciesToTokens(rows) {
    if (!rows || !rows.length) return [];
    return rows.map(function (row) {
      var headId = null;
      if (row.relation !== 'root' && row.head != null) {
        headId = row.head - 1;
      }
      return {
        id: row.id - 1,
        text: row.text,
        lemma: row.lemma || '',
        tag: row.pos || '',
        pos: '',
        pos_label: row.pos || '',
        dep: row.relation || 'dep',
        head_id: headId,
      };
    });
  }

  function buildTreeFromFlatTokens(tokens) {
    if (!tokens || !tokens.length) return null;
    var n = tokens.length;
    var children = [];
    var i;
    for (i = 0; i < n; i++) children.push([]);
    var root = 0;
    tokens.forEach(function (t, idx) {
      var h = t.head_id;
      if (h === null || h === undefined) root = idx;
      else if (h >= 0 && h < n) children[h].push(idx);
    });
    function build(i) {
      var t = tokens[i];
      return {
        text: t.text,
        dep: t.dep || '',
        pos_label: t.pos_label || t.tag || '',
        children: children[i]
          .slice()
          .sort(function (a, b) {
            return a - b;
          })
          .map(build),
      };
    }
    return build(root);
  }

  function renderHierarchy(el, tree) {
    if (!tree || !Object.keys(tree).length) {
      el.innerHTML = '<p class="text-muted mb-0">No nested tree (heuristic mode).</p>';
      return;
    }
    function walk(node) {
      var ul = document.createElement('ul');
      ul.className = 'dep-tree-list';
      var li = document.createElement('li');
      li.innerHTML =
        '<span class="dep-tree-token">' +
        escapeXml(node.text) +
        '</span> ' +
        '<span class="text-muted small">(' +
        escapeXml(node.dep || '') +
        ')</span> ' +
        '<span class="badge bg-secondary">' +
        escapeXml(node.pos_label || '') +
        '</span>';
      if (node.children && node.children.length) {
        node.children.forEach(function (ch) {
          li.appendChild(walk(ch));
        });
      }
      ul.appendChild(li);
      return ul;
    }
    el.innerHTML = '';
    el.appendChild(walk(tree));
  }

  function renderConstituentTree(el, tree) {
    if (!tree || !Object.keys(tree).length) {
      el.innerHTML = '<p class="text-muted mb-0">No constituent tree available.</p>';
      return;
    }

    function walk(node) {
      var ul = document.createElement('ul');
      ul.className = 'dep-tree-list';

      var li = document.createElement('li');
      var parts = [
        '<span class="badge text-bg-primary me-2">' + escapeXml(node.label || '') + '</span>',
      ];

      if (node.text) {
        parts.push('<span class="dep-tree-token">' + escapeXml(node.text) + '</span>');
      } else {
        parts.push('<span class="text-muted small">constituent</span>');
      }

      li.innerHTML = parts.join('');

      if (node.children && node.children.length) {
        node.children.forEach(function (child) {
          li.appendChild(walk(child));
        });
      }

      ul.appendChild(li);
      return ul;
    }

    el.innerHTML = '';
    el.appendChild(walk(tree));
  }

  function init() {
    var el = document.getElementById('syntax-payload-json');
    if (!el) return;
    var payload;
    try {
      payload = JSON.parse(el.textContent);
    } catch (e) {
      return;
    }
    var dep = payload.dependency_parse || {};
    var constituentTree = payload.constituent_tree || {};
    var tokens = dep.tokens || [];
    if (!tokens.length && payload.dependencies && payload.dependencies.length) {
      tokens = legacyDependenciesToTokens(payload.dependencies);
    }
    var tree = dep.tree;
    if ((!tree || !Object.keys(tree).length) && tokens.length) {
      tree = buildTreeFromFlatTokens(tokens);
    }
    var arcHost = document.getElementById('dependency-tree-arcs');
    var hierHost = document.getElementById('dependency-tree-hierarchy');
    var constituentHost = document.getElementById('constituent-tree-hierarchy');
    if (arcHost) renderArcDiagram(arcHost, tokens);
    if (hierHost) renderHierarchy(hierHost, tree);
    if (constituentHost) renderConstituentTree(constituentHost, constituentTree);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
