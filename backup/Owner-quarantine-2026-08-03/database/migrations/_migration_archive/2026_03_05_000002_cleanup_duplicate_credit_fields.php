<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * 
     * 清理重複的信用控制欄位
     * - 移除 credit_value（與 credit_amount 重複）
     * - 保留 coin_value 和 credit_amount 作為標準欄位
     */
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // 移除重複的 credit_value 欄位
            $table->dropColumn('credit_value');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // 恢復 credit_value 欄位（如果需要回滾）
            $table->unsignedInteger('credit_value')->default(100)->after('pulse_ratio');
        });
    }
};
