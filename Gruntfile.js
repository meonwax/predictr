'use strict';

module.exports = function(grunt) {
  require('load-grunt-tasks')(grunt);

  grunt.initConfig({
    dirs: {
        app: 'src/main/webapp'
    },
    wiredep: {
      task: {
        src: '<%= dirs.app %>/index.html'
      }
    },
    sass: {
      options: {
        loadPath: 'node_modules/bootstrap-sass/assets/stylesheets'
      },
      dev: {
        files: {
          '<%= dirs.app %>/css/style.css': 'src/main/scss/style.scss'
        },
        options: {
          style: 'expanded'
        }
      },
      dist: {
        files: {
          '<%= dirs.app %>/css/style.css': 'src/main/scss/style.scss'
        },
        options: {
          style: 'compressed',
          sourcemap: 'none'
        }
      }
    },
    browserSync: {
      bsFiles: {
        src: [
          '<%= dirs.app %>/*.html',
          '<%= dirs.app %>/css/**/*.css',
          '<%= dirs.app %>/images/**/*.{png,jpg,jpeg,gif,webp,svg}',
          '<%= dirs.app %>/js/**/*.js',
          '<%= dirs.app %>/templates/*.html',
          '<%= dirs.app %>/values/**/*.{md,json}'
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
    'sass:dev',
    'wiredep',
    'browserSync'
  ]);

  grunt.registerTask('build', [
    'sass:dist',
  ]);

  grunt.registerTask('default', [
    'build'
  ]);
};
