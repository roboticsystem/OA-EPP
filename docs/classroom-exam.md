# 课堂在线考试

正在跳转到考试页面…

若未自动跳转，请点击：

- **本地开发**：[http://127.0.0.1:8009/classroom-exam](http://127.0.0.1:8009/classroom-exam)
- **线上环境**：[/classroom-exam](/classroom-exam)

<script>
(function () {
  var isLocal = location.hostname === "127.0.0.1" || location.hostname === "localhost";
  var base = isLocal ? "http://127.0.0.1:8009" : "";
  location.replace(base + "/classroom-exam");
})();
</script>
