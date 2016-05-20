'use strict';

module.exports = function(grunt) {
  require('load-grunt-tasks')(grunt);

  grunt.initConfig({
    dirs: {
      app: 'src/main/webapp',
      scss: 'src/main/scss'
    },
    clean: [
      '.sass-cache',
      '<%= dirs.app %>/css/'
    ],
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
          '<%= dirs.app %>/css/style.css': '<%= dirs.scss %>/style.scss'
        },
        options: {
          style: 'expanded'
        }
      },
      dist: {
        files: {
          '<%= dirs.app %>/css/style.css': '<%= dirs.scss %>/style.scss'
        },
        options: {
          style: 'compressed',
          sourcemap: 'none'
        }
      }
    },
    watch: {
      bower: {
        files: 'bower.json',
        tasks: ['wiredep']
      },
      sass: {
        files: '<%= dirs.scss %>/*.scss',
        tasks: ['sass:dev']
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
        watchTask: true,
        proxy: 'localhost:8081',
        open: false
      }
    }
  });

  grunt.registerTask('serve', [
    'sass:dev',
    'wiredep',
    'browserSync',
    'watch'
  ]);

  grunt.registerTask('build', [
    'clean',
    'sass:dist',
    'wiredep'
  ]);

  grunt.registerTask('default', [
    'build'
  ]);
};
