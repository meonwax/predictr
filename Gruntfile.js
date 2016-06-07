'use strict';

module.exports = function(grunt) {
  require('load-grunt-tasks')(grunt);

  grunt.initConfig({
    dirs: {
      app: 'src/main/webapp',
      dist: 'src/main/webapp/dist',
      scss: 'src/main/scss'
    },
    clean: [
      '.sass-cache',
      '.tmp',
      '<%= dirs.app %>/css/',
      '<%= dirs.dist %>'
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
    },
    copy: {
      dist: {
        files: [{
          expand: true,
          // dot: true,
          cwd: '<%= dirs.app %>',
          dest: '<%= dirs.dist %>',
          src: [
            '*.html',
            'images/**/*.{png,gif}',
            'templates/*.html',
            'values/*.{json,md}',
            'favicon.ico',
            'robots.txt'
          ]
        }, {
          expand: true,
          cwd: '<%= dirs.app %>/lib/components-font-awesome',
          dest: '<%= dirs.dist %>',
          src: [
            'fonts/**/*.{eot,svg,ttf,woff,woff2}'
          ]
        }]
      }
    },
    useminPrepare: {
      html: '<%= dirs.app %>/index.html',
      options: {
        dest: '<%= dirs.dist %>',
        flow: {
          html: {
            steps: {
              js: ['uglifyjs'],
              css: ['cssmin']
            }
          }
        }
      }
    },
    usemin: {
      html: ['<%= dirs.dist %>/*.html'],
      js: ['<%= dirs.dist %>/js/**/*.js'],
      css: ['<%= dirs.dist %>/css/*.css'],
      options: {
        dirs: ['<%= dirs.app %>']
      }
    },
    ngAnnotate: {
      options: {
        singleQuotes: true
      },
      dist: {
        files: [{
          expand: true,
          cwd: '<%= dirs.app %>/js',
          src: '**/*.js',
          dest: '.tmp/js'
        }]
      }
    },
    uglify: {
      options: {
        compress: {
          drop_console: true
        }
      }
    },
    htmlmin: {
      dist: {
        options: {
        removeComments: true,
        collapseWhitespace: true,
        //conservativeCollapse: true,
        },
        files: {
          '<%= dirs.dist %>/index.html': '<%= dirs.dist %>/index.html'
        }
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
    'wiredep',
    'useminPrepare',
    'copy:dist',
    'cssmin',
    'ngAnnotate:dist',
    'uglify',
    'usemin',
    'htmlmin'
  ]);

  grunt.registerTask('default', [
    'build'
  ]);
};
