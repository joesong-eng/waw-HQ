<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // 添加 credit_value 欄位：每次開分命令觸發的金額（分）
            // 預設 100 分 = 1 元
            $table->unsignedInteger('credit_value')->default(100)->after('pulse_ratio');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn('credit_value');
        });
    }
};
