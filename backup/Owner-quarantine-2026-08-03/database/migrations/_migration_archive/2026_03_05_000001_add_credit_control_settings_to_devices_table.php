<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * 
     * 新增信用控制相關設定欄位
     * - coin_value: y = 代幣面額（元/幣）- 每個硬幣代表多少元
     * - credit_amount: z = 開分金額（元/次）- 按一下開分鍵增加多少元
     * 
     * 計算公式：開分觸發次數 = credit_amount ÷ coin_value
     * 範例：100元開分 ÷ 10元/幣 = 10次觸發
     */
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // y = 代幣面額（元/幣）
            $table->unsignedInteger('coin_value')
                ->default(10)
                ->after('pulse_ratio')
                ->comment('代幣面額（元/幣），每個硬幣代表多少元');
            
            // z = 開分金額（元/次）
            $table->unsignedInteger('credit_amount')
                ->default(100)
                ->after('coin_value')
                ->comment('開分金額（元/次），按一下開分鍵增加多少元');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn(['coin_value', 'credit_amount']);
        });
    }
};
