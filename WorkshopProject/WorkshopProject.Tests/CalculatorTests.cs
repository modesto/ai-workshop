namespace WorkshopProject.Tests;

using AwesomeAssertions;
using WorkshopProject.Core;

public class CalculatorTests
{
    [Fact]
    public void VerificaSuma_NumerosPositivos_RetornaResultadoCorrecto()
    {
        // Arrange
        var calculadora = new Calculator();
        int numero1 = 5;
        int numero2 = 3;
        int resultadoEsperado = 8;

        // Act
        int resultado = calculadora.Sum(numero1, numero2);

        // Assert
        Assert.Equal(resultadoEsperado, resultado);
    }


}