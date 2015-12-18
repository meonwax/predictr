'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'ngCookies', 'ngResource'])
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

    /*
    * Routes
    */
    $routeProvider
      .when('/', {
        templateUrl: 'templates/home.html',
        controller: 'HomeCtrl',
        activeTab: 'home'
      })
      .when('/bets', {
        templateUrl: 'templates/bets.html',
        controller: 'BetsCtrl',
        activeTab: 'bets'
      })
      .when('/ladder', {
        templateUrl: 'templates/ladder.html',
        controller: 'LadderCtrl',
        activeTab: 'ladder'
      })
      .when('/questions', {
        templateUrl: 'templates/questions.html',
        controller: 'QuestionsCtrl',
        activeTab: 'questions'
      })
      .when('/rules', {
        templateUrl: 'templates/rules.html',
        controller: 'RulesCtrl',
        activeTab: 'rules'
      })
      .when('/shoutbox', {
        templateUrl: 'templates/shoutbox.html',
        controller: 'ShoutboxCtrl',
        activeTab: 'shoutbox'
      })
      .when('/admin', {
        templateUrl: 'templates/admin.html',
        controller: 'AdminCtrl',
        activeTab: 'admin'
      })
      .otherwise({
        redirectTo: '/'
      });

    /*
    * I18n
    */
    $translateProvider
      .useStaticFilesLoader({
        prefix: 'data/i18n-',
        suffix: '.json'
      })
      .preferredLanguage('de')
      .useCookieStorage()
      .useSanitizeValueStrategy('escapeParameters');
  });
