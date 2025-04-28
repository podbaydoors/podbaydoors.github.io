<script>
document.addEventListener('DOMContentLoaded', () => {
  // 1. find every thumbnail on the page
  document.querySelectorAll('.video-thumb').forEach(thumb => {
    thumb.addEventListener('click', () => {
      // 2. instantiate the template
      const tpl = document.getElementById('video-modal-template');
      const node = tpl.content.cloneNode(true);
      const backdrop = node.querySelector('.video-backdrop');

      // 3. inject into <body>
      document.body.appendChild(node);

      // 4. close when clicking outside the video
      backdrop.addEventListener('click', e => {
        if (e.target === backdrop) backdrop.remove();
      });
    });
  });
});
</script>