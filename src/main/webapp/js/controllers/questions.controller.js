'use strict';

angular.module('predictrApp')
  .controller('QuestionsCtrl', function($rootScope, $scope, $translate, toastr, $uibModal, Question, questions, Answer) {

    $rootScope.loading = false;

    $scope.questions = questions;
    $scope.deadlinePassed = Question.deadlinePassed;

    $scope.send = function() {
      $scope.saving = true;

      // Prepare DTO array to save
      var answerDtos = [];
      angular.forEach($scope.questions, function(question) {
        var answer = question.answers[0];
        if (answer) {
          answerDtos.push({
            'answer': answer.answer,
            'question': {
              'id': question.id
            }
          });
        }
      });

      // Actually save it
      Answer.save(answerDtos,
        function() {
          toastr.success($translate.instant('bets.saveOk'));
          $scope.saving = false;
        },
        function(response) {
          var errorMessage = $translate.instant('bets.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.saving = false;
        }
      );
    };

    $scope.showOther = function(question) {

      // Inline modal controller function
      var otherAnswersCtrl = function($scope, $uibModalInstance) {
        $scope.question = question;
        $scope.deadlinePassed = Question.deadlinePassed(question);
        if($scope.deadlinePassed) {
          Answer.query({questionId: question.id}, function(result) {
            $scope.answers = result;
          });
        }
        $scope.ok = function () {
          $uibModalInstance.close();
        };
      };

      // Open the modal dialog
      $uibModal.open({
        templateUrl: 'templates/otheranswers.html',
        controller: otherAnswersCtrl
      });
    };
  });
