'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'ngCookies', 'ngResource', 'angular-ladda'])
  .run(function($rootScope, $route, $translate, ServerInfo, Account) {
    // Initialize root scope
    $rootScope.$route = $route;
    $rootScope.serverInfo = ServerInfo.get();
    $rootScope.account = Account.get();
    $rootScope.changeLanguage = function(language) {
      $translate.use(language);
    };
  })
  .config(function($routeProvider, $translateProvider) {
    // I18n
    $translateProvider
      .useStaticFilesLoader({
        prefix: 'values/strings-',
        suffix: '.json'
      })
      .preferredLanguage('de')
      .useCookieStorage()
      .useSanitizeValueStrategy('escapeParameters');
  });
