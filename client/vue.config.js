module.exports = {
  devServer: {
    port: 8081,
      public: process.env.PUBLIC_ADDRESS
    },
    publicPath: process.env.VUE_APP_STATIC_PATH,
  lintOnSave: false
}
