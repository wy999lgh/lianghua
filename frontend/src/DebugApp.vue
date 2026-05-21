<template>
  <div style="max-width: 800px; margin: 50px auto; padding: 20px; font-family: Arial, sans-serif;">
    <h1 style="color: #4f46e5;">✅ Vue 应用测试</h1>
    <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
      <h3>✅ Vue 已正确加载！</h3>
      <p>如果您看到这个页面，说明 Vue 应用正常工作。</p>
    </div>
    <div style="background: #fff3cd; padding: 20px; border-radius: 8px;">
      <h3>📋 状态检查：</h3>
      <ul>
        <li><strong>后端API：</strong> <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a></li>
        <li><strong>前端服务：</strong> http://localhost:3000</li>
        <li><strong>当前时间：</strong> {{ currentTime }}</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DebugApp',
  data() {
    return {
      currentTime: new Date().toLocaleString()
    }
  },
  mounted() {
    setInterval(() => {
      this.currentTime = new Date().toLocaleString()
    }, 1000)
  }
}
</script>

<style>
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}
</style>
