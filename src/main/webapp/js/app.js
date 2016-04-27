'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'ngCookies', 'ngResource', 'LocalStorageModule', 'angular-ladda', 'ngAnimate', 'toastr'])
  .run(function($rootScope, $route, $translate, $location, ServerInfo, Authentication) {

    // Initialize root scope
    $rootScope.$route = $route;
    $rootScope.serverInfo = ServerInfo.get();

    $rootScope.changeLanguage = function(language) {
      $translate.use(language);
    };

    $rootScope.logout = function() {
      Authentication.logout();
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
