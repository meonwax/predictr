'use strict';

module.exports = function(grunt) {
  require('load-grunt-tasks')(grunt);

  grunt.initConfig({
    wiredep: {
      task: {
        src: 'src/main/webapp/index.html'
      }
    },
    browserSync: {
      bsFiles: {
        src: [
          'src/main/webapp/*.html',
          'src/main/webapp/css/**/*.css',
          'src/main/webapp/images/**/*.{png,jpg,jpeg,gif,webp,svg}',
          'src/main/webapp/js/**/*.js',
          'src/main/webapp/templates/*.html',
          'src/main/webapp/values/**/*.{md,json}'
        ]
      },
      options: {
        //watchTask: true,
        proxy: 'localhost:8081',
        open: false
      }
    }
  });

  grunt.registerTask('serve', [
    'wiredep',
    'browserSync'
  ]);

  grunt.registerTask('build', function() {
    grunt.log.writeln('Building not implemented yet.');
  });

  grunt.registerTask('default', [
    'build'
  ]);
};
