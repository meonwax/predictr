'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'angularMoment', 'ngCookies', 'ngResource', 'LocalStorageModule', 'angular-ladda', 'ngAnimate', 'smoothScroll', 'toastr', 'ui.bootstrap'])
  .run(function($rootScope, $route, $location, $translate, amMoment, ServerInfo, Authentication, User, ROLES) {

    // Initialize root scope
    $rootScope.ROLES = ROLES;
    $rootScope.$route = $route;
    ServerInfo.get().get(function(serverInfo) {
      $rootScope.serverInfo = serverInfo;
      $rootScope.serverClock = ServerInfo.serverClock().init(serverInfo.time);
    });

    User.account().get(function(user) {
      $translate.use(user.preferredLanguage);
      amMoment.changeLocale(user.preferredLanguage);
      $rootScope.account = user;
    });

    $rootScope.logout = function() {
      Authentication.logout();
      $rootScope.account = null;
      $location.path('login');
    };

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
