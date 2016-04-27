'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/questions', {
      templateUrl: 'templates/questions.html',
      controller: 'QuestionsCtrl',
      activeTab: 'questions',
      resolve: {
        questions: function($q, Question) {
          var deferred = $q.defer();
          Question.query(function(questions) {
            deferred.resolve(questions);
          });
          return deferred.promise;
        }
      }
    });
  });
