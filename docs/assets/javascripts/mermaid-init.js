document.addEventListener('DOMContentLoaded', function() {
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
      },
      sequence: {
        showSequenceNumbers: false,
        wrap: true
      }
    });
    
    setTimeout(function() {
      var codeElements = document.querySelectorAll('code');
      var mermaidIndex = 0;
      
      codeElements.forEach(function(element) {
        var text = element.textContent || element.innerText;
        if (text.trim().startsWith('sequenceDiagram') || 
            text.trim().startsWith('flowchart') ||
            text.trim().startsWith('graph') ||
            text.trim().startsWith('classDiagram') ||
            text.trim().startsWith('stateDiagram') ||
            text.trim().startsWith('gantt') ||
            text.trim().startsWith('pie')) {
          
          var id = 'mermaid-' + mermaidIndex;
          mermaidIndex++;
          
          var div = document.createElement('div');
          div.id = id;
          div.className = 'mermaid';
          div.innerHTML = text;
          
          var parent = element.closest('pre, div.highlight');
          if (parent) {
            parent.parentNode.replaceChild(div, parent);
          }
        }
      });
      
      if (mermaidIndex > 0) {
        mermaid.init();
      }
    }, 200);
  }
});
