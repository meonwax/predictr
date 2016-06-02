'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'ngCookies', 'ngResource', 'LocalStorageModule', 'angular-ladda', 'ngAnimate', 'toastr', 'ui.bootstrap'])
  .run(function($rootScope, $route, $location, ServerInfo, Authentication, User, ROLES) {

    // Initialize root scope
    $rootScope.$route = $route;
    $rootScope.serverInfo = ServerInfo.get();
    $rootScope.ROLES = ROLES;

    $rootScope.logout = function() {
      Authentication.logout();
      $rootScope.account = null;
      $location.path('login');
    }

    $rootScope.Auth = Authentication;
  })
  .config(function($httpProvider, $translateProvider, localStorageServiceProvider, toastrConfig) {

    // Register http interceptor for handling AJAX errors
    $httpProvider.interceptors.push('HttpInterceptorService');

    // I18n
    $translateProvider
      .useStaticFilesLoader({
        prefix: 'values/strings-',
        suffix: '.json'
      })
      // TODO: Determine initial language by browser setting
      .preferredLanguage('de')
      .useCookieStorage()
      .useSanitizeValueStrategy('escapeParameters');

    // Local storage
    localStorageServiceProvider
      .setPrefix('predictr')
      .setStorageType('sessionStorage');

    //Toastr
    angular.extend(toastrConfig, {
      allowHtml: true,
      timeOut: 3000,
      preventOpenDuplicates: true,
    });
  });
